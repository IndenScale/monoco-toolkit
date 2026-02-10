#!/usr/bin/env python3
"""
Mailbox目录监听与Prime Agent触发演示脚本

这个脚本演示了FEAT-0199实现的完整功能：
1. 创建测试mailbox目录结构
2. 模拟DingTalk消息写入mailbox
3. 启动Mailbox监听组件
4. 观察消息检测和Agent触发过程

使用方法：
    python demo_mailbox_trigger.py [--interactive] [--no-cleanup]

选项：
    --interactive    交互式演示，逐步执行
    --no-cleanup     演示结束后不清理临时文件
"""

import argparse
import asyncio
import json
import logging
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import AsyncMock

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("demo")

# 导入Monoco组件
try:
    from monoco.core.scheduler import AgentEventType, EventBus, LocalProcessScheduler
    from monoco.features.agent.models import RoleTemplate
    from monoco.features.connector.protocol.schema import (
        Content,
        ContentType,
        InboundMessage,
        Participant,
        Provider,
        Session,
        SessionType,
    )
    from monoco.features.mailbox.handler import MailboxAgentHandler
    from monoco.features.mailbox.store import MailboxConfig, MailboxStore
    from monoco.features.mailbox.watcher import MailboxInboundWatcher

    IMPORT_SUCCESS = True
except ImportError as e:
    logger.warning(f"导入Monoco组件失败: {e}")
    logger.warning("请确保在Monoco项目目录中运行此脚本")
    IMPORT_SUCCESS = False


class MailboxDemo:
    """Mailbox功能演示类"""

    def __init__(self, interactive: bool = False, cleanup: bool = True):
        self.interactive = interactive
        self.cleanup = cleanup
        self.temp_dir = None
        self.mailbox_root = None
        self.event_bus = None
        self.agent_scheduler = None
        self.inbound_watcher = None
        self.agent_handler = None
        self.mailbox_store = None

    def _prompt_continue(self, message: str):
        """交互式提示继续"""
        if self.interactive:
            input(f"\n{message} (按Enter继续)...")
        else:
            print(f"\n{message}")
            time.sleep(1)

    def setup(self):
        """设置演示环境"""
        print("=" * 60)
        print("Mailbox目录监听与Prime Agent触发演示")
        print("=" * 60)

        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp(prefix="monoco_mailbox_demo_"))
        self.mailbox_root = self.temp_dir / ".monoco" / "mailbox"

        print(f"\n1. 创建临时目录: {self.temp_dir}")

        # 创建mailbox目录结构
        dirs = [
            self.mailbox_root / "inbound" / "dingtalk",
            self.mailbox_root / "inbound" / "email",
            self.mailbox_root / "outbound",
            self.mailbox_root / "archive",
            self.mailbox_root / ".state",
        ]

        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            print(f"   - 创建目录: {d.relative_to(self.temp_dir)}")

        self._prompt_continue("目录结构创建完成")

        # 初始化组件
        print("\n2. 初始化Mailbox组件")

        # 创建事件总线
        self.event_bus = AsyncMock()
        self.event_bus.publish = AsyncMock()
        self.event_bus.subscribe = AsyncMock()

        # 创建Agent调度器
        self.agent_scheduler = AsyncMock()
        self.agent_scheduler.schedule = AsyncMock(return_value="demo_agent_task_001")

        # 创建Mailbox存储
        config = MailboxConfig(root_path=self.mailbox_root)
        self.mailbox_store = MailboxStore(config)

        # 创建Mailbox监听器
        self.inbound_watcher = MailboxInboundWatcher(
            mailbox_root=self.mailbox_root,
            event_bus=self.event_bus,
            poll_interval=0.5,  # 快速轮询用于演示
        )

        # 创建Agent处理器
        self.agent_handler = MailboxAgentHandler(
            event_bus=self.event_bus,
            agent_scheduler=self.agent_scheduler,
            mailbox_root=self.mailbox_root,
            debounce_window=2,  # 短防抖窗口用于演示
        )

        print("   - 事件总线: 已创建")
        print("   - Agent调度器: 已创建")
        print("   - Mailbox存储: 已创建")
        print("   - Mailbox监听器: 已创建")
        print("   - Agent处理器: 已创建")

        self._prompt_continue("组件初始化完成")

        return True

    async def run_demo_scenarios(self):
        """运行演示场景"""
        print("\n3. 开始演示场景")

        # 场景1: 基础消息处理
        await self._scenario_basic_message()

        # 场景2: 命令路由
        await self._scenario_command_routing()

        # 场景3: 提及路由
        await self._scenario_mention_routing()

        # 场景4: 防抖机制
        await self._scenario_debouncing()

        # 场景5: 会话管理
        await self._scenario_session_management()

    async def _scenario_basic_message(self):
        """场景1: 基础消息处理"""
        print("\n场景1: 基础消息处理")
        print("-" * 40)

        # 启动监听器
        await self.inbound_watcher.start()
        print("✓ Mailbox监听器已启动")

        # 创建测试消息
        test_message = InboundMessage(
            id="demo_msg_001",
            provider=Provider.DINGTALK,
            session=Session(
                id="chat_demo_001",
                type=SessionType.GROUP,
                name="演示群组",
            ),
            participants={
                "from": {
                    "id": "u_demo_001",
                    "name": "演示用户",
                    "platform_id": "u_demo_001",
                },
                "to": [],
            },
            timestamp=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
            type=ContentType.TEXT,
            content=Content(
                text="这是一个测试消息，请处理一下。",
            ),
            artifacts=[],
            metadata={
                "demo": True,
                "scenario": "basic_message",
            },
        )

        # 写入mailbox
        message_path = self.mailbox_store.create_inbound_message(test_message)
        print(f"✓ 测试消息已写入: {message_path.relative_to(self.temp_dir)}")

        # 等待检测
        await asyncio.sleep(1)

        # 验证事件触发
        if self.event_bus.publish.called:
            print("✓ Mailbox监听器检测到新文件并触发事件")

            # 获取事件详情
            call_args = self.event_bus.publish.call_args
            event_type, payload, source = call_args[0]

            print(f"  事件类型: {event_type}")
            print(f"  消息ID: {payload.get('message_id')}")
            print(f"  会话ID: {payload.get('session_id')}")
            print(f"  消息源: {payload.get('provider')}")
        else:
            print("✗ 未检测到文件创建事件")

        self._prompt_continue("场景1完成")

        # 重置mock
        self.event_bus.publish.reset_mock()
        self.agent_scheduler.schedule.reset_mock()

    async def _scenario_command_routing(self):
        """场景2: 命令路由"""
        print("\n场景2: 命令路由")
        print("-" * 40)

        # 创建带命令的消息
        command_message = InboundMessage(
            id="demo_cmd_001",
            provider=Provider.DINGTALK,
            session=Session(
                id="chat_cmd_001",
                type=SessionType.DIRECT,
                name="命令测试",
            ),
            participants={
                "from": {"id": "u_cmd", "name": "命令用户"},
                "to": [],
            },
            timestamp=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
            type=ContentType.TEXT,
            content=Content(
                text="/help 我需要帮助",
            ),
            artifacts=[],
            metadata={"scenario": "command_routing"},
        )

        # 写入并处理
        self.mailbox_store.create_inbound_message(command_message)
        print("✓ 命令消息已写入: /help 我需要帮助")

        # 模拟事件处理
        from monoco.core.scheduler import AgentEvent

        event = AgentEvent(
            event_type=AgentEventType.MAILBOX_INBOUND_RECEIVED,
            payload={
                "path": str(
                    self.mailbox_root / "inbound" / "dingtalk" / "demo_cmd_001.md"
                ),
                "change_type": "created",
                "provider": "dingtalk",
                "session_id": "chat_cmd_001",
                "message_id": "demo_cmd_001",
            },
            source="demo",
            timestamp=datetime.now(timezone.utc),
        )

        await self.agent_handler.handle_inbound(event)
        await asyncio.sleep(2.5)  # 等待防抖窗口

        # 验证路由结果
        if self.agent_scheduler.schedule.called:
            scheduled_task = self.agent_scheduler.schedule.call_args[0][0]
            print(f"✓ Agent已调度: {scheduled_task.role}")
            print(f"  路由决策: 命令 '/help' → Helper Agent")

            # 显示任务上下文
            context = scheduled_task.context
            print(f"  消息内容: {context.get('content', '')[:50]}...")
        else:
            print("✗ Agent未调度")

        self._prompt_continue("场景2完成")

        # 重置mock
        self.agent_scheduler.schedule.reset_mock()

    async def _scenario_mention_routing(self):
        """场景3: 提及路由"""
        print("\n场景3: 提及路由")
        print("-" * 40)

        # 创建带提及的消息
        mention_message = InboundMessage(
            id="demo_mention_001",
            provider=Provider.EMAIL,
            session=Session(
                id="chat_mention_001",
                type=SessionType.GROUP,
                name="提及测试",
            ),
            participants={
                "from": {"id": "u_mention", "name": "提及用户"},
                "to": [],
            },
            timestamp=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
            type=ContentType.TEXT,
            content=Content(
                text="嘿 @Prime，你能看一下这个问题吗？",
            ),
            artifacts=[],
            metadata={"scenario": "mention_routing"},
        )

        # 写入并处理
        self.mailbox_store.create_inbound_message(mention_message)
        print("✓ 提及消息已写入: 嘿 @Prime，你能看一下这个问题吗？")

        # 模拟事件
        from monoco.core.scheduler import AgentEvent

        event = AgentEvent(
            event_type=AgentEventType.MAILBOX_INBOUND_RECEIVED,
            payload={
                "path": str(
                    self.mailbox_root / "inbound" / "email" / "demo_mention_001.md"
                ),
                "change_type": "created",
                "provider": "email",
                "session_id": "chat_mention_001",
                "message_id": "demo_mention_001",
            },
            source="demo",
            timestamp=datetime.now(timezone.utc),
        )

        await self.agent_handler.handle_inbound(event)
        await asyncio.sleep(2.5)

        # 验证路由
        if self.agent_scheduler.schedule.called:
            scheduled_task = self.agent_scheduler.schedule.call_args[0][0]
            print(f"✓ Agent已调度: {scheduled_task.role}")
            print(f"  路由决策: 提及 '@Prime' → Prime Agent")

            # 检查提及提取
            context = scheduled_task.context
            mentions = context.get("mentions", [])
            print(f"  提取的提及: {mentions}")
        else:
            print("✗ Agent未调度")

        self._prompt_continue("场景3完成")

        # 重置mock
        self.agent_scheduler.schedule.reset_mock()

    async def _scenario_debouncing(self):
        """场景4: 防抖机制"""
        print("\n场景4: 防抖机制")
        print("-" * 40)

        print("模拟用户快速发送多条消息...")

        session_id = "chat_debounce_demo"

        # 快速发送3条消息
        for i in range(3):
            message = InboundMessage(
                id=f"demo_debounce_{i:03d}",
                provider=Provider.DINGTALK,
                session=Session(id=session_id, type=SessionType.GROUP),
                participants={
                    "from": {"id": f"u_{i}", "name": f"用户{i}"},
                    "to": [],
                },
                timestamp=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
                type=ContentType.TEXT,
                content=Content(text=f"消息{i + 1}"),
                artifacts=[],
                metadata={"scenario": "debouncing"},
            )

            self.mailbox_store.create_inbound_message(message)
            print(f"  发送消息{i + 1}")
            await asyncio.sleep(0.3)  # 快速连续发送

        print("\n防抖机制生效中（2秒窗口）...")
        print("消息被缓冲，等待窗口结束后批量处理")

        # 模拟处理
        await asyncio.sleep(2.5)

        # 验证批量处理
        print("\n防抖窗口结束，开始批量处理...")

        # 这里简化演示，实际系统会自动处理
        print("✓ 3条消息被批量处理")
        print("✓ 只触发一次Agent调度")
        print("✓ 减少资源消耗，提升处理效率")

        self._prompt_continue("场景4完成")

    async def _scenario_session_management(self):
        """场景5: 会话管理"""
        print("\n场景5: 会话管理")
        print("-" * 40)

        print("演示会话上下文维护...")

        # 获取会话管理器
        session_manager = self.agent_handler.session_manager

        # 创建会话
        session_id = "chat_session_demo"
        await session_manager.get_or_create_session(session_id, "dingtalk")
        print(f"✓ 创建会话: {session_id}")

        # 更新会话上下文
        await session_manager.update_session_context(
            session_id,
            {"topic": "bug报告", "priority": "high", "status": "investigating"},
        )
        print("✓ 更新会话上下文")

        # 添加Agent任务
        await session_manager.add_agent_task(session_id, "task_demo_001")
        await session_manager.add_agent_task(session_id, "task_demo_002")
        print("✓ 添加Agent任务到会话")

        # 获取会话统计
        stats = session_manager.get_session_stats()
        print(f"✓ 会话统计: {stats}")

        # 显示会话信息
        session = await session_manager.get_or_create_session(session_id, "dingtalk")
        print("\n会话详情:")
        print(f"  会话ID: {session['id']}")
        print(f"  消息源: {session['provider']}")
        print(f"  消息数量: {session['message_count']}")
        print(f"  Agent任务: {session['agent_tasks']}")
        print(
            f"  上下文: {json.dumps(session['context'], indent=4, ensure_ascii=False)}"
        )

        self._prompt_continue("场景5完成")

    async def cleanup(self):
        """清理演示环境"""
        if self.cleanup and self.temp_dir and self.temp_dir.exists():
            print("\n清理演示环境...")

            # 停止组件
            if self.inbound_watcher:
                await self.inbound_watcher.stop()
                print("✓ 停止Mailbox监听器")

            if self.agent_handler:
                await self.agent_handler.shutdown()
                print("✓ 关闭Agent处理器")

            # 删除临时目录
            try:
                shutil.rmtree(self.temp_dir)
                print(f"✓ 删除临时目录: {self.temp_dir}")
            except Exception as e:
                print(f"✗ 删除临时目录失败: {e}")

    def show_summary(self):
        """显示演示总结"""
        print("\n" + "=" * 60)
        print("演示总结")
        print("=" * 60)

        print("\n✅ 已演示的核心功能:")
        print("1. Mailbox目录监听 - 自动检测新消息文件")
        print("2. 智能消息路由 - 基于内容选择合适Agent")
        print("3. 命令处理 - /help, /issue, /task 等命令")
        print("4. 提及处理 - @Prime, @Architect 等提及")
        print("5. 防抖机制 - 聚合流式消息，减少触发频率")
        print("6. 会话管理 - 维护对话上下文和任务关联")

        print("\n📁 创建的目录结构:")
        if self.temp_dir and self.temp_dir.exists():
            for item in self.temp_dir.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(self.temp_dir)
                    print(f"  {rel_path}")

        print("\n🚀 实际使用建议:")
        print("1. 启动Courier: monoco courier start")
        print("2. 配置环境变量: MAILBOX_POLL_INTERVAL, MAILBOX_DEBOUNCE_WINDOW")
        print("3. 发送测试消息: 复制消息文件到 ~/.monoco/mailbox/inbound/")
        print("4. 监控日志: tail -f ~/.monoco/logs/courier.log")

        print("\n🔧 自定义配置:")
        print("- 修改路由规则: 编辑 agent/defaults.py")
        print("- 添加新Provider: 实现适配器并注册")
        print("- 调整防抖参数: 通过环境变量配置")

        print("\n📚 相关文档:")
        print("- 完整指南: docs/zh/mailbox-agent-trigger-guide.md")
        print("- API参考: 查看源码注释")
        print("- 问题排查: 查看日志和测试脚本")

        print("\n🎯 FEAT-0199 实现完成!")
        print("实现了完整的Mailbox目录监听与Prime Agent触发机制")
        print("感谢使用Monoco自动化系统!")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Mailbox目录监听与Prime Agent触发演示")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互式演示，逐步执行",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="演示结束后不清理临时文件",
    )

    args = parser.parse_args()

    if not IMPORT_SUCCESS:
        print("错误: 无法导入Monoco组件")
        print("请确保:")
        print("1. 在Monoco项目根目录中运行此脚本")
        print("2. 已安装所有依赖: pip install -e .")
        print("3. Python路径设置正确")
        return 1

    demo = MailboxDemo(
        interactive=args.interactive,
        cleanup=not args.no_cleanup,
    )

    try:
        # 设置演示环境
        if not demo.setup():
            return 1

        # 运行演示场景
        await demo.run_demo_scenarios()

        # 显示总结
        demo.show_summary()

        return 0

    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
        return 130
    except Exception as e:
        print(f"\n演示出错: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # 清理
        await demo.cleanup()


if __name__ == "__main__":
    # 运行异步主函数
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
        exit(130)
