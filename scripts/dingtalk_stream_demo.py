#!/usr/bin/env python3
"""
钉钉 Stream 模式演示脚本

使用方法:
1. 设置环境变量:
   export DINGTALK_APP_KEY="your-app-key"
   export DINGTALK_APP_SECRET="your-app-secret"

2. 运行:
   python scripts/dingtalk_stream_demo.py
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from monoco.features.courier.adapters.dingtalk_stream import (
    create_dingtalk_stream_adapter,
    DingTalkStreamAdapter,
)


def print_banner():
    """打印启动横幅"""
    print("""
╔══════════════════════════════════════════╗
║     Monoco DingTalk Stream 演示          ║
║     无需公网 IP 接收钉钉消息              ║
╚══════════════════════════════════════════╝
    """)


def get_credentials():
    """从环境变量或输入获取凭证"""
    app_key = os.environ.get("DINGTALK_APP_KEY")
    app_secret = os.environ.get("DINGTALK_APP_SECRET")
    
    if not app_key:
        app_key = input("请输入钉钉 AppKey: ").strip()
    if not app_secret:
        app_secret = input("请输入钉钉 AppSecret: ").strip()
    
    return app_key, app_secret


def on_message_received(message, project_slug):
    """消息接收回调"""
    sender = message.participants.get("from", {})
    sender_name = sender.get("name", "Unknown")
    content = message.content.text or message.content.markdown or "[无文本内容]"
    
    print(f"\n📩 收到新消息")
    print(f"   项目: {project_slug}")
    print(f"   发送者: {sender_name}")
    print(f"   内容: {content[:100]}{'...' if len(content) > 100 else ''}")
    print(f"   时间: {message.timestamp}")
    print(f"   ID: {message.id}")
    print("-" * 50)


async def main():
    """主函数"""
    print_banner()
    
    # 获取凭证
    app_key, app_secret = get_credentials()
    
    if not app_key or not app_secret:
        print("❌ 错误: 需要提供 AppKey 和 AppSecret")
        print("\n获取方式:")
        print("1. 登录钉钉开放平台: https://open.dingtalk.com/")
        print("2. 创建企业内部应用")
        print("3. 启用机器人功能，选择 Stream 模式")
        print("4. 在应用详情页获取 AppKey 和 AppSecret")
        sys.exit(1)
    
    print(f"\n🔑 使用 AppKey: {app_key[:10]}...")
    print("📡 正在连接钉钉 Stream 服务器...")
    print("(按 Ctrl+C 退出)\n")
    
    # 创建适配器
    adapter = create_dingtalk_stream_adapter(
        app_key=app_key,
        app_secret=app_secret,
        default_project="demo",
    )
    
    # 设置消息处理器
    adapter.set_message_handler(on_message_received)
    
    try:
        # 连接并监听
        await adapter.connect()
        print("✅ 连接成功！等待消息...\n")
        
        # 持续监听
        async for message in adapter.listen():
            # 消息已通过回调处理，这里只是保持循环
            pass
            
    except KeyboardInterrupt:
        print("\n\n👋 正在关闭连接...")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await adapter.disconnect()
        print("✅ 已断开连接")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n已退出")
