> ## 文档索引
> 访问完整文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件发现所有可用页面。

# Hooks 参考指南

> 关于 Claude Code hook 事件、配置模式、JSON 输入/输出格式、退出代码、异步 hook、提示词 hook 以及 MCP 工具 hook 的参考资料。

<Tip>
  有关包含示例的快速入门指南，请参阅[使用 hooks 自动化工作流](/en/hooks-guide)。
</Tip>

Hooks 是用户定义的 Shell 命令或 LLM 提示词，它们在 Claude Code 生命周期的特定点自动执行。使用此参考指南查找事件模式、配置选项、JSON 输入/输出格式，以及异步 hook 和 MCP 工具 hook 等高级功能。如果您是第一次设置 hooks，请先从[指南](/en/hooks-guide)开始。

## Hook 生命周期

Hooks 在 Claude Code 会话期间的特定点触发。当事件触发且匹配器（matcher）匹配时，Claude Code 会将有关该事件的 JSON 上下文传递给您的 hook 处理器。对于命令 hooks，这通过 stdin 传入。您的处理器可以随后检查输入、采取行动，并可选地返回决策。某些事件每个会话仅触发一次，而其他事件则在代理循环内部反复触发：

<div style={{maxWidth: "500px", margin: "0 auto"}}>
  <Frame>
    <img src="https://mintcdn.com/claude-code/z2YM37Ycg6eMbID3/images/hooks-lifecycle.png?fit=max&auto=format&n=z2YM37Ycg6eMbID3&q=85&s=5c25fedbc3db6f8882af50c3cc478c32" alt="Hook 生命周期图，显示了从 SessionStart 经过代理循环到 SessionEnd 的 hook 序列" data-og-width="8876" width="8876" data-og-height="12492" height="12492" data-path="images/hooks-lifecycle.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/claude-code/z2YM37Ycg6eMbID3/images/hooks-lifecycle.png?w=280&fit=max&auto=format&n=z2YM37Ycg6eMbID3&q=85&s=62406fcd5d4a189cc8842ee1bd946b84 280w, https://mintcdn.com/claude-code/z2YM37Ycg6eMbID3/images/hooks-lifecycle.png?w=560&fit=max&auto=format&n=z2YM37Ycg6eMbID3&q=85&s=fa3049022a6973c5f974e0f95b28169d 560w, https://mintcdn.com/claude-code/z2YM37Ycg6eMbID3/images/hooks-lifecycle.png?w=840&fit=max&auto=format&n=z2YM37Ycg6eMbID3&q=85&s=bd2890897db61a03160b93d4f972ff8e 840w, https://mintcdn.com/claude-code/z2YM37Ycg6eMbID3/images/hooks-lifecycle.png?w=1100&fit=max&auto=format&n=z2YM37Ycg6eMbID3&q=85&s=7ae8e098340479347135e39df4a13454 1100w, https://mintcdn.com/claude-code/z2YM37Ycg6eMbID3/images/hooks-lifecycle.png?w=1650&fit=max&auto=format&n=z2YM37Ycg6eMbID3&q=85&s=848a8606aab22c2ccaa16b6a18431e32 1650w, https://mintcdn.com/claude-code/z2YM37Ycg6eMbID3/images/hooks-lifecycle.png?w=2500&fit=max&auto=format&n=z2YM37Ycg6eMbID3&q=85&s=f3a9ef7feb61fa8fe362005aa185efbc 2500w" />
  </Frame>
</div>

下表总结了每个事件触发的时间。[Hook 事件](#hook-events)部分记录了每个事件的完整输入模式和决策控制选项。

| 事件                 | 触发时机                                             |
| :------------------- | :--------------------------------------------------- |
| `SessionStart`       | 当会话开始或恢复时                                   |
| `UserPromptSubmit`   | 当您提交提示词时，在 Claude 处理它之前               |
| `PreToolUse`         | 在工具调用执行之前。可以拦截它                       |
| `PermissionRequest`  | 当权限对话框出现时                                   |
| `PostToolUse`        | 在工具调用成功后                                     |
| `PostToolUseFailure` | 在工具调用失败后                                     |
| `Notification`       | 当 Claude Code 发送通知时                            |
| `SubagentStart`      | 当启动子代理（subagent）时                           |
| `SubagentStop`       | 当子代理完成任务时                                   |
| `Stop`               | 当 Claude 完成响应时                                 |
| `PreCompact`         | 在上下文压缩（compaction）之前                       |
| `SessionEnd`         | 当会话终止时                                         |

### Hook 如何解析

为了了解这些部分是如何协同工作的，请考虑这个拦截破坏性 Shell 命令的 `PreToolUse` hook。该 hook 在每个 Bash 工具调用之前运行 `block-rm.sh`：

```json  theme={null}
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/block-rm.sh"
          }
        ]
      }
    ]
  }
}
```

该脚本从 stdin 读取 JSON 输入，提取命令，如果包含 `rm -rf`，则返回 `"deny"` 的 `permissionDecision`：

```bash  theme={null}
#!/bin/bash
# .claude/hooks/block-rm.sh
COMMAND=$(jq -r '.tool_input.command')

if echo "$COMMAND" | grep -q 'rm -rf'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "破坏性命令已被 hook 拦截"
    }
  }'
else
  exit 0  # 允许该命令
fi
```

现在假设 Claude Code 决定运行 `Bash "rm -rf /tmp/build"`。以下是发生的事情：

<Frame>
  <img src="https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=7c13f51ffcbc37d22a593b27e2f2de72" alt="Hook 解析流程：PreToolUse 事件触发，匹配器检查 Bash 是否匹配，hook 处理器运行，结果返回到 Claude Code" data-og-width="780" width="780" data-og-height="290" height="290" data-path="images/hook-resolution.svg" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=280&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=36a39a07e8bc1995dcb4639e09846905 280w, https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=560&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=6568d90c596c7605bbac2c325b0a0c86 560w, https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=840&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=255a6f68b9475a0e41dbde7b88002dad 840w, https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=1100&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=dcecf8d5edc88cd2bc49deb006d5760d 1100w, https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=1650&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=04fe51bf69ae375e9fd517f18674e35f 1650w, https://mintcdn.com/claude-code/s7NM0vfd_wres2nf/images/hook-resolution.svg?w=2500&fit=max&auto=format&n=s7NM0vfd_wres2nf&q=85&s=b1b76e0b77fddb5c7fa7bf302dacd80b 2500w" />
</Frame>

<Steps>
  <Step title="事件触发">
    `PreToolUse` 事件触发。Claude Code 将工具输入以 JSON 格式通过 stdin 发送给 hook：

    ```json  theme={null}
    { "tool_name": "Bash", "tool_input": { "command": "rm -rf /tmp/build" }, ... }
    ```
  </Step>

  <Step title="匹配器检查">
    匹配器 `"Bash"` 匹配该工具名称，因此 `block-rm.sh` 开始运行。如果您省略匹配器或使用 `"*"`，则该 hook 会在该事件的每次发生时运行。只有当定义了匹配器且不匹配时，hook 才会跳过。
  </Step>

  <Step title="Hook 处理器运行">
    脚本从输入中提取 `"rm -rf /tmp/build"` 并匹配到 `rm -rf`，因此它将决策打印到 stdout：

    ```json  theme={null}
    {
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "破坏性命令已被 hook 拦截"
      }
    }
    ```

    如果命令是安全的（如 `npm test`），脚本将执行 `exit 0`，这会告知 Claude Code 在无需进一步操作的情况下允许该工具调用。
  </Step>

  <Step title="Claude Code 根据结果执行操作">
    Claude Code 读取 JSON 决策，拦截该工具调用，并向 Claude 显示拦截原因。
  </Step>
</Steps>

下面的[配置](#configuration)部分文档记录了完整模式，每个 [hook 事件](#hook-events)部分文档记录了您的命令接收什么输入以及可以返回什么输出。

## 配置

Hooks 在 JSON 设置文件中定义。配置有三个层级的嵌套：

1. 选择一个 [hook 事件](#hook-events)进行响应，如 `PreToolUse` 或 `Stop`
2. 添加一个 [匹配器组 (matcher group)](#matcher-patterns) 来过滤它何时触发，例如“仅针对 Bash 工具”
3. 定义一个或多个匹配时运行的 [hook 处理器 (hook handlers)](#hook-handler-fields)

有关带注释示例的完整演练，请参阅上面的 [Hook 如何解析](#how-a-hook-resolves)。

<Note>
  本页对每个层级使用特定术语：**hook 事件 (hook event)** 表示生命周期点，**匹配器组 (matcher group)** 表示过滤器，**hook 处理器 (hook handler)** 表示运行的 Shell 命令、提示词或代理。“Hook”本身是指通用功能。
</Note>

### Hook 位置

定义 hook 的位置决定了它的作用域：

| 位置                                                         | 作用域                         | 是否可共享                         |
| :----------------------------------------------------------- | :----------------------------- | :--------------------------------- |
| `~/.claude/settings.json`                                    | 您的所有项目                   | 否，仅限您的本地机器               |
| `.claude/settings.json`                                      | 单个项目                       | 是，可以提交到代码库               |
| `.claude/settings.local.json`                                | 单个项目                       | 否，被 git 忽略                    |
| 托管策略设置                                                 | 整个组织                       | 是，由管理员控制                   |
| [插件](/en/plugins) `hooks/hooks.json`                       | 当插件启用时                   | 是，随插件捆绑                     |
| [Skill](/en/skills) 或 [代理](/en/sub-agents) 的 frontmatter | 当该组件处于活动状态时         | 是，在组件文件中定义               |

有关设置文件解析的详细信息，请参阅 [settings](/en/settings)。企业管理员可以使用 `allowManagedHooksOnly` 来禁用用户、项目和插件 hook。请参阅 [Hook 配置](/en/settings#hook-configuration)。

### 匹配模式

`matcher` 字段是一个正则表达式字符串，用于过滤 hook 何时触发。使用 `"*"`、`""` 或完全省略 `matcher` 来匹配所有发生情况。每种事件类型在不同的字段上进行匹配：

| 事件                                                                   | 匹配器过滤的内容          | 匹配器示例值                                                                   |
| :--------------------------------------------------------------------- | :------------------------ | :----------------------------------------------------------------------------- |
| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest` | 工具名称                  | `Bash`, `Edit\|Write`, `mcp__.*`                                               |
| `SessionStart`                                                         | 会话如何启动              | `startup`, `resume`, `clear`, `compact`                                        |
| `SessionEnd`                                                           | 会话为何结束              | `clear`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` |
| `Notification`                                                         | 通知类型                  | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`       |
| `SubagentStart`                                                        | 代理类型                  | `Bash`, `Explore`, `Plan`, 或自定义代理名称                                    |
| `PreCompact`                                                           | 什么触发了压缩            | `manual`, `auto`                                                               |
| `SubagentStop`                                                         | 代理类型                  | 与 `SubagentStart` 相同的值                                                    |
| `UserPromptSubmit`, `Stop`                                             | 不支持匹配器              | 始终在每次发生时触发                                                           |

匹配器是正则表达式，因此 `Edit|Write` 匹配这两个工具中的任何一个，`Notebook.*` 匹配任何以 Notebook 开头的工具。匹配器针对 Claude Code 通过 stdin 发送给 hook 的 [JSON 输入](#hook-input-and-output)中的某个字段运行。对于工具事件，该字段是 `tool_name`。每个 [hook 事件](#hook-events)部分列出了该事件的完整匹配器值集和输入模式。

此示例仅在 Claude 写入或编辑文件时运行 linting 脚本：

```json  theme={null}
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/lint-check.sh"
          }
        ]
      }
    ]
  }
}
```

`UserPromptSubmit` 和 `Stop` 不支持匹配器，并且始终在每次发生时触发。如果您为这些事件添加 `matcher` 字段，它会被静默忽略。

#### 匹配 MCP 工具

[MCP](/en/mcp) 服务器工具在工具事件（`PreToolUse`、`PostToolUse`、`PostToolUseFailure`、`PermissionRequest`）中表现为常规工具，因此您可以像匹配任何其他工具名称一样匹配它们。

MCP 工具遵循命名模式 `mcp__<server>__<tool>`，例如：

* `mcp__memory__create_entities`: Memory 服务器的 create entities 工具
* `mcp__filesystem__read_file`: Filesystem 服务器的 read file 工具
* `mcp__github__search_repositories`: GitHub 服务器的 search 工具

使用正则表达式模式针对特定的 MCP 工具或工具组：

* `mcp__memory__.*` 匹配 `memory` 服务器的所有工具
* `mcp__.*__write.*` 匹配任何服务器中包含 "write" 的任何工具

此示例记录了所有 memory 服务器操作并验证了来自任何 MCP 服务器的写入操作：

```json  theme={null}
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__memory__.*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Memory operation initiated' >> ~/mcp-operations.log"
          }
        ]
      },
      {
        "matcher": "mcp__.*__write.*",
        "hooks": [
          {
            "type": "command",
            "command": "/home/user/scripts/validate-mcp-write.py"
          }
        ]
      }
    ]
  }
}
```

### Hook 处理器字段

内部 `hooks` 数组中的每个对象都是一个 hook 处理器：当匹配器匹配时运行的 Shell 命令、LLM 提示词或代理。共有三种类型：

* **[命令 hook](#command-hook-fields)** (`type: "command"`): 运行一个 Shell 命令。您的脚本通过 stdin 接收事件的 [JSON 输入](#hook-input-and-output)，并通过退出代码和 stdout 反馈结果。
* **[提示词 hook](#prompt-and-agent-hook-fields)** (`type: "prompt"`): 将提示词发送给 Claude 模型进行单轮评估。模型以 JSON 格式返回是/否决策。参见 [基于提示词的 hooks](#prompt-based-hooks)。
* **[代理 hook](#prompt-and-agent-hook-fields)** (`type: "agent"`): 启动一个子代理，该子代理可以使用 Read、Grep 和 Glob 等工具在返回决策之前验证条件。参见 [基于代理的 hooks](#agent-based-hooks)。

#### 通用字段

这些字段适用于所有 hook 类型：

| 字段            | 是否必填 | 描述                                                                                                                                           |
| :-------------- | :------- | :--------------------------------------------------------------------------------------------------------------------------------------------- |
| `type`          | 是       | `"command"`, `"prompt"`, 或 `"agent"`                                                                                                          |
| `timeout`       | 否       | 取消前的秒数。默认值：命令为 600，提示词为 30，代理为 60                                                                                       |
| `statusMessage` | 否       | hook 运行时显示的自定义加载消息                                                                                                                |
| `once`          | 否       | 如果为 `true`，则每个会话仅运行一次然后被移除。仅限 Skills，不适用于代理。参见 [Skills 和代理中的 Hooks](#hooks-in-skills-and-agents) |

#### 命令 hook 字段

除了 [通用字段](#common-fields) 外，命令 hook 还接受以下字段：

| 字段      | 是否必填 | 描述                                                                                                     |
| :-------- | :------- | :------------------------------------------------------------------------------------------------------- |
| `command` | 是       | 要执行的 Shell 命令                                                                                      |
| `async`   | 否       | 如果为 `true`，则在后台运行而不阻塞。参见 [在后台运行 hooks](#run-hooks-in-the-background) |

#### 提示词和代理 hook 字段

除了 [通用字段](#common-fields) 外，提示词和代理 hook 还接受以下字段：

| 字段     | 是否必填 | 描述                                                                           |
| :------- | :------- | :----------------------------------------------------------------------------- |
| `prompt` | 是       | 发送给模型的提示词文本。使用 `$ARGUMENTS` 作为 hook 输入 JSON 的占位符         |
| `model`  | 否       | 用于评估的模型。默认为快速模型                                                 |

所有匹配的 hook 都会并行运行，相同的处理器会自动去重。处理器在 Claude Code 环境下的当前目录中运行。环境变量 `$CLAUDE_CODE_REMOTE` 在远程 Web 环境中设置为 `"true"`，在本地 CLI 中不设置。

### 通过路径引用脚本

使用环境变量引用相对于项目或插件根目录的 hook 脚本，而无需考虑运行 hook 时的当前工作目录：

* `$CLAUDE_PROJECT_DIR`: 项目根目录。用引号括起来以处理包含空格的路径。
* `${CLAUDE_PLUGIN_ROOT}`: 插件的根目录，用于随 [插件](/en/plugins) 捆绑的脚本。

<Tabs>
  <Tab title="项目脚本">
    此示例使用 `$CLAUDE_PROJECT_DIR` 在任何 `Write` 或 `Edit` 工具调用后运行来自项目的 `.claude/hooks/` 目录的代码风格检查器：

    ```json  theme={null}
    {
      "hooks": {
        "PostToolUse": [
          {
            "matcher": "Write|Edit",
            "hooks": [
              {
                "type": "command",
                "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-style.sh"
              }
            ]
          }
        ]
      }
    }
    ```
  </Tab>
  <Tab title="插件脚本">
    在 `hooks/hooks.json` 中定义插件 hook，并带有一个可选的顶层 `description` 字段。当插件启用时，其 hook 将与您的用户和项目 hook 合并。

    此示例运行随插件捆绑的格式化脚本：

    ```json  theme={null}
    {
      "description": "自动代码格式化",
      "hooks": {
        "PostToolUse": [
          {
            "matcher": "Write|Edit",
            "hooks": [
              {
                "type": "command",
                "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
                "timeout": 30
              }
            ]
          }
        ]
      }
    }
    ```

    有关创建插件 hook 的详细信息，请参阅[插件组件参考](/en/plugins-reference#hooks)。
  </Tab>
</Tabs>

### Skills 和代理中的 Hooks

除了设置文件和插件外，还可以使用 frontmatter 直接在 [skills](/en/skills) 和 [子代理（subagents）](/en/sub-agents) 中定义 hook。这些 hook 的作用域限定在该组件的生命周期内，且仅在该组件处于活动状态时运行。

支持所有 hook 事件。对于子代理，`Stop` hook 会自动转换为 `SubagentStop`，因为这是子代理完成时触发的事件。

Hooks 使用与基于设置的 hook 相同的配置格式，但作用域限定在组件的生命周期内，并在其完成时清理。

此 skill 定义了一个 `PreToolUse` hook，在每个 `Bash` 命令之前运行安全验证脚本：

```yaml  theme={null}
---
name: secure-operations
description: Perform operations with security checks
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
---
```

代理在其 YAML frontmatter 中使用相同的格式。

### `/hooks` 菜单

在 Claude Code 中输入 `/hooks` 以打开交互式 hook 管理器，您可以在其中查看、添加和删除 hook，而无需直接编辑设置文件。有关逐步操作说明，请参阅指南中的[设置您的第一个 hook](/en/hooks-guide#set-up-your-first-hook)。

菜单中的每个 hook 都带有一个方括号前缀，指示其来源：

* `[User]`: 来自 `~/.claude/settings.json`
* `[Project]`: 来自 `.claude/settings.json`
* `[Local]`: 来自 `.claude/settings.local.json`
* `[Plugin]`: 来自插件的 `hooks/hooks.json`，只读

### 禁用或删除 hook

要删除 hook，请从设置 JSON 文件中删除其条目，或使用 `/hooks` 菜单并选择要删除的 hook。

要临时禁用所有 hook 而不删除它们，请在设置文件中设置 `"disableAllHooks": true` 或使用 `/hooks` 菜单中的切换开关。目前无法在保留配置的同时禁用单个 hook。

直接编辑设置文件中的 hook 不会立即生效。Claude Code 会在启动时捕获 hook 的快照，并在整个会话期间使用它。这可以防止恶意或意外的 hook 修改在您未审核的情况下在会话中期生效。如果 hook 在外部被修改，Claude Code 会发出警告，并要求在 `/hooks` 菜单中进行审核，然后更改才会生效。

## Hook 输入和输出

Hooks 通过 stdin 接收 JSON 数据，并通过退出代码、stdout 和 stderr 通信结果。本节涵盖所有事件共有的字段和行为。每个事件在 [Hook 事件](#hook-events) 下的章节都包含了其特定的输入模式和决策控制选项。

### 通用输入字段

除了在每个 [hook 事件](#hook-events) 章节中记录的特定于事件的字段外，所有 hook 事件都通过 stdin 作为 JSON 接收这些字段：

| 字段              | 描述                                                                                                                                     |
| :---------------- | :--------------------------------------------------------------------------------------------------------------------------------------- |
| `session_id`      | 当前会话标识符                                                                                                                           |
| `transcript_path` | 会话 JSON 的路径                                                                                                                         |
| `cwd`             | 调用 hook 时的工作目录                                                                                                                   |
| `permission_mode` | 当前[权限模式](/en/permissions#permission-modes)：`"default"`, `"plan"`, `"acceptEdits"`, `"dontAsk"`, 或 `"bypassPermissions"` |
| `hook_event_name` | 触发的事件名称                                                                                                                           |

例如，Bash 命令的 `PreToolUse` hook 会在 stdin 上接收到：

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/home/user/.claude/projects/.../transcript.jsonl",
  "cwd": "/home/user/my-project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test"
  }
}
```

`tool_name` 和 `tool_input` 字段是特定于事件的。每个 [hook 事件](#hook-events) 章节都记录了该事件的其他字段。

### 退出代码输出

hook 命令的退出代码会告知 Claude Code 是继续、锁定还是忽略该操作。

**退出代码 0** 表示成功。Claude Code 会解析 stdout 以获取 [JSON 输出字段](#json-output)。JSON 输出仅在退出代码为 0 时处理。对于大多数事件，stdout 仅在详细模式 (`Ctrl+O`) 下显示。例外情况是 `UserPromptSubmit` 和 `SessionStart`，它们的 stdout 会作为上下文添加，供 Claude 查看和采取行动。

**退出代码 2** 表示阻塞性错误。Claude Code 会忽略 stdout 及其中的任何 JSON。相反，stderr 文本会反馈给 Claude 作为错误消息。其效果取决于事件：`PreToolUse` 阻塞工具调用，`UserPromptSubmit` 拒绝提示词，依此类推。请参阅[每个事件的退出代码 2 行为](#exit-code-2-behavior-per-event)获取完整列表。

**任何其他退出代码** 均为非阻塞性错误。stderr 会在详细模式 (`Ctrl+O`) 下显示，执行将继续。

例如，一个拦截危险 Bash 命令的 hook 命令脚本：

```bash  theme={null}
#!/bin/bash
# 从 stdin 读取 JSON 输入，检查命令
command=$(jq -r '.tool_input.command' < /dev/stdin)

if [[ "$command" == rm* ]]; then
  echo "Blocked: rm commands are not allowed" >&2
  exit 2  # 阻塞性错误：阻止工具调用
fi

exit 0  # 成功：工具调用继续进行
```

#### 每个事件的退出代码 2 行为

退出代码 2 是 hook 发出“停止，不要这样做”信号的方式。其效果取决于事件，因为某些事件代表可以被阻塞的操作（例如尚未发生的工具调用），而另一些事件则代表已经发生或无法阻止的事情。

| Hook 事件            | 是否可以阻塞？ | 退出代码 2 时发生的情况                   |
| :------------------- | :------------- | :---------------------------------------- |
| `PreToolUse`         | 是             | 阻塞工具调用                              |
| `PermissionRequest`  | 是             | 拒绝权限                                  |
| `UserPromptSubmit`   | 是             | 阻塞提示词处理并清除提示词                |
| `Stop`               | 是             | 阻止 Claude 停止，继续对话                |
| `SubagentStop`       | 是             | 阻止子代理停止                            |
| `PostToolUse`        | 否             | 向 Claude 显示 stderr（工具已运行）       |
| `PostToolUseFailure` | 否             | 向 Claude 显示 stderr（工具已失败）       |
| `Notification`       | 否             | 仅向用户显示 stderr                       |
| `SubagentStart`      | 否             | 仅向用户显示 stderr                       |
| `SessionStart`       | 否             | 仅向用户显示 stderr                       |
| `SessionEnd`         | 否             | 仅向用户显示 stderr                       |
| `PreCompact`         | 否             | 仅向用户显示 stderr                       |

### JSON 输出

退出代码允许您授权或阻塞，但 JSON 输出可以提供更细粒度的控制。与其使用代码 2 退出以进行阻塞，不如执行退出 0 并将 JSON 对象打印到 stdout。Claude Code 从该 JSON 中读取特定字段以控制行为，包括用于阻塞、允许或升级给用户的[决策控制](#decision-control)。

<Note>
  每个 hook 您必须选择一种方式，而不能两者兼具：要么仅使用退出代码进行信号传递，要么执行退出 0 并打印 JSON 以进行结构化控制。Claude Code 仅在退出代码为 0 时处理 JSON。如果您执行退出 2，任何 JSON 都会被忽略。
</Note>

您的 hook stdout 必须仅包含 JSON 对象。如果您的 shell 配置文件在启动时打印文本内容，可能会干扰 JSON 解析。请参阅故障排除指南中的 [JSON 验证失败](/en/hooks-guide#json-validation-failed)。

JSON 对象支持三种字段：

* **通用字段** (如 `continue`) 可在所有事件中使用。这些字段在下表中列出。
* **顶层 `decision` 和 `reason`** 被某些事件用于阻塞或提供反馈。
* **`hookSpecificOutput`** 是一个嵌套对象，用于需要更丰富控制的事件。它需要将 `hookEventName` 字段设置为事件名称。

| 字段            | 默认值  | 描述                                                                            |
| :-------------- | :------ | :------------------------------------------------------------------------------ |
| `continue`       | `true`  | 如果为 `false`，Claude 在 hook 运行后将完全停止处理。优先级高于任何特定于事件的决策字段 |
| `stopReason`     | 无      | 当 `continue` 为 `false` 时向用户显示的消息。不会显示给 Claude                  |
| `suppressOutput` | `false` | 如果为 `true`，则在详细模式输出中隐藏 stdout                                    |
| `systemMessage`  | 无      | 向用户显示的警告消息                                                            |

要停止 Claude（无论事件类型如何）：

```json  theme={null}
{ "continue": false, "stopReason": "构建失败，请在继续之前修复错误" }
```

#### 决策控制

并非每个事件都支持通过 JSON 阻塞或控制行为。支持该功能的事件各自使用不同的字段集来表达该决策。在编写 hook 前，请使用此表作为快速参考：

| 事件                                                                  | 决策模式             | 关键字段                                                          |
| :-------------------------------------------------------------------- | :------------------- | :---------------------------------------------------------------- |
| UserPromptSubmit, PostToolUse, PostToolUseFailure, Stop, SubagentStop | 顶层 `decision`      | `decision: "block"`, `reason`                                     |
| PreToolUse                                                            | `hookSpecificOutput` | `permissionDecision` (allow/deny/ask), `permissionDecisionReason` |
| PermissionRequest                                                     | `hookSpecificOutput` | `decision.behavior` (allow/deny)                                  |

以下是每种模式的实际应用示例：

<Tabs>
  <Tab title="顶层决策">
    用于 `UserPromptSubmit`、`PostToolUse`、`PostToolUseFailure`、`Stop` 和 `SubagentStop`。唯一的值是 `"block"` —— 要允许操作继续，请从 JSON 中省略 `decision`，或以 0 状态码退出且不返回任何 JSON：

    ```json  theme={null}
    {
      "decision": "block",
      "reason": "在继续之前测试套件必须通过"
    }
    ```
  </Tab>

  <Tab title="PreToolUse">
    使用 `hookSpecificOutput` 进行更丰富的控制：允许 (allow)、拒绝 (deny) 或升级给用户 (ask)。您还可以在工具运行前修改其输入，或为 Claude 注入额外的上下文。请参阅 [PreToolUse 决策控制](#pretooluse-decision-control) 了解完整选项集。

    ```json  theme={null}
    {
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "不允许数据库写入操作"
      }
    }
    ```
  </Tab>

  <Tab title="PermissionRequest">
    使用 `hookSpecificOutput` 代表用户允许或拒绝权限请求。在允许时，您还可以修改工具的输入或应用权限规则，以便不再提示用户。请参阅 [PermissionRequest 决策控制](#permissionrequest-decision-control) 了解完整选项集。

    ```json  theme={null}
    {
      "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
          "behavior": "allow",
          "updatedInput": {
            "command": "npm run lint"
          }
        }
      }
    }
    ```
  </Tab>
</Tabs>

对于包括 Bash 命令验证、提示词过滤和自动批准脚本在内的扩展示例，请参阅指南中的[您可以自动化什么](/en/hooks-guide#what-you-can-automate)以及 [Bash 命令验证器参考实现](https://github.com/anthropics/claude-code/blob/main/examples/hooks/bash_command_validator_example.py)。

## Hook 事件

每个事件对应 Claude Code 生命周期中可以运行 hook 的一个点。下面的章节按生命周期顺序排列：从会话设置到代理循环再到会话结束。每个部分描述了事件触发的时机、支持的匹配器、接收的 JSON 输入以及如何通过输出来控制行为。

### SessionStart

在 Claude Code 启动新会话或恢复现有会话时运行。适用于加载开发上下文（如现有 issue 或代码库的近期更改）或设置环境变量。对于不需要脚本的静态上下文，请改用 [CLAUDE.md](/en/memory)。

SessionStart 在每个会话中都会运行，因此请保持此类 hook 运行迅速。

匹配器值对应于会话的启动方式：

| 匹配器   | 触发时机                               |
| :------- | :------------------------------------- |
| `startup` | 新会话                                 |
| `resume`  | `--resume`、`--continue` 或 `/resume` |
| `clear`   | `/clear`                               |
| `compact` | 自动或手动压缩（compaction）           |

#### SessionStart 输入

除了[通用输入字段](#common-input-fields)外，SessionStart hook 还会收到 `source`、`model` 以及可选的 `agent_type`。`source` 字段指示会话如何启动：新会话为 `"startup"`，恢复的会话为 `"resume"`，`/clear` 后为 `"clear"`，压缩后为 `"compact"`。`model` 字段包含模型标识符。如果您使用 `claude --agent <name>` 启动 Claude Code，`agent_type` 字段则包含代理名称。

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SessionStart",
  "source": "startup",
  "model": "claude-sonnet-4-5-20250929"
}
```

#### SessionStart 决策控制

您的 hook 脚本打印到 stdout 的任何文本都会作为 Claude 的上下文添加。除了所有 hook 可用的 [JSON 输出字段](#json-output)外，您还可以返回这些事件特定字段：

| 字段               | 描述                                                       |
| :----------------- | :--------------------------------------------------------- |
| `additionalContext` | 添加到 Claude 上下文的字符串。多个 hook 的值将被连接在一起 |

```json  theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "这里是我的附加上下文"
  }
}
```

#### 持久化环境变量

SessionStart hook 可以访问 `CLAUDE_ENV_FILE` 环境变量，该变量提供了一个文件路径，您可以在其中为随后的 Bash 命令持久化环境变量。

要设置单个环境变量，请向 `CLAUDE_ENV_FILE` 写入 `export` 语句。使用追加重定向 (`>>`) 以保留其他 hook 设置的变量：

```bash  theme={null}
#!/bin/bash

if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
  echo 'export DEBUG_LOG=true' >> "$CLAUDE_ENV_FILE"
  echo 'export PATH="$PATH:./node_modules/.bin"' >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

要捕获设置命令引起的所有环境更改，请比较导出变量前后的状态：

```bash  theme={null}
#!/bin/bash

ENV_BEFORE=$(export -p | sort)

# 运行修改环境的设置命令
source ~/.nvm/nvm.sh
nvm use 20

if [ -n "$CLAUDE_ENV_FILE" ]; then
  ENV_AFTER=$(export -p | sort)
  comm -13 <(echo "$ENV_BEFORE") <(echo "$ENV_AFTER") >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

写入此文件的任何变量都将在 Claude Code 在会话期间执行的所有后续 Bash 命令中可用。

<Note>
  `CLAUDE_ENV_FILE` 仅适用于 SessionStart hook。其他类型的 hook 无法访问此变量。
</Note>

### UserPromptSubmit

在用户提交提示词之后、Claude 处理它之前运行。这允许您根据提示词/对话添加额外的上下文、验证提示词或阻塞某些类型的提示词。

#### UserPromptSubmit 输入

除了[通用输入字段](#common-input-fields)外，UserPromptSubmit hook 还会收到包含用户提交文本的 `prompt` 字段。

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "编写一个函数来计算数字的阶乘"
}
```

#### UserPromptSubmit 决策控制

`UserPromptSubmit` hook 可以控制用户提示词是否被处理并添加上下文。所有 [JSON 输出字段](#json-output) 均可用。

在退出码为 0 时，有两种方式向对话添加上下文：

* **纯文本 stdout**: 写入 stdout 的任何非 JSON 文本都会作为上下文添加。
* **带 `additionalContext` 的 JSON**: 使用下面的 JSON 格式进行更多控制。`additionalContext` 字段会被作为上下文添加。

纯文本 stdout 在对话记录中显示为 hook 输出。`additionalContext` 字段的添加则更为隐蔽。

要阻塞提示词，请返回一个 `decision` 设置为 `"block"` 的 JSON 对象：

| 字段               | 描述                                                                            |
| :----------------- | :------------------------------------------------------------------------------ |
| `decision`         | `"block"` 阻止提示词被处理并将其从上下文中擦除。省略则允许提示词继续处理        |
| `reason`           | 当 `decision` 为 `"block"` 时向用户显示。不会被添加到上下文                     |
| `additionalContext` | 被添加到 Claude 上下文的字符串                                                  |

```json  theme={null}
{
  "decision": "block",
  "reason": "决策的解释",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "这里是我的附加上下文"
  }
}
```

<Note>
  对于简单的用例，不需要 JSON 格式。要添加上下文，您可以在退出码为 0 的情况下打印纯文本到 stdout。当您需要阻塞提示词或需要更结构化的控制时，请使用 JSON。
</Note>

### PreToolUse

在 Claude 创建工具参数后、处理工具调用前运行。匹配工具名称：`Bash`、`Edit`、`Write`、`Read`、`Glob`、`Grep`、`Task`、`WebFetch`、`WebSearch` 以及任何 [MCP 工具名称](#match-mcp-tools)。

使用 [PreToolUse 决策控制](#pretooluse-decision-control) 来允许、拒绝或请求使用工具的权限。

#### PreToolUse 输入

除了[通用输入字段](#common-input-fields)外，PreToolUse hook 还会收到 `tool_name`、`tool_input` 和 `tool_use_id`。`tool_input` 字段取决于具体的工具：

##### Bash

执行 Shell 命令。

| 字段               | 类型    | 示例               | 描述                           |
| :----------------- | :------ | :----------------- | :----------------------------- |
| `command`           | string  | `"npm test"`       | 要执行的 Shell 命令            |
| `description`       | string  | `"运行测试套件"`   | 该命令功能的可选描述           |
| `timeout`           | number  | `120000`           | 可选的超时时间（毫秒）         |
| `run_in_background` | boolean | `false`            | 是否在后台运行命令             |

##### Write

创建或覆盖文件。

| 字段        | 类型   | 示例                  | 描述                           |
| :---------- | :----- | :-------------------- | :----------------------------- |
| `file_path` | string | `"/path/to/file.txt"` | 要写入的文件的绝对路径         |
| `content`   | string | `"文件内容"`          | 要写入文件的内容               |

##### Edit

替换现有文件中的字符串。

| 字段          | 类型    | 示例                  | 描述                           |
| :------------ | :------ | :-------------------- | :----------------------------- |
| `file_path`   | string  | `"/path/to/file.txt"` | 要编辑的文件的绝对路径         |
| `old_string`  | string  | `"原始文本"`          | 要查找并替换的文本             |
| `new_string`  | string  | `"替换文本"`          | 替换后的文本                   |
| `replace_all` | boolean | `false`               | 是否替换所有出现的地方         |

##### Read

读取文件内容。

| 字段        | 类型   | 示例                  | 描述                           |
| :---------- | :----- | :-------------------- | :----------------------------- |
| `file_path` | string | `"/path/to/file.txt"` | 要读取的文件的绝对路径         |
| `offset`    | number | `10`                  | 可选的起始读取行号             |
| `limit`     | number | `50`                  | 可选的读取行数                 |

##### Glob

查找匹配 glob 模式的文件。

| 字段      | 类型   | 示例             | 描述                                       |
| :-------- | :----- | :--------------- | :----------------------------------------- |
| `pattern` | string | `"**/*.ts"`      | 用于匹配文件的 glob 模式                   |
| `path`    | string | `"/path/to/dir"` | 可选的搜索目录。默认为当前工作目录         |

##### Grep

使用正则表达式搜索文件内容。

| 字段          | 类型    | 示例             | 描述                                                                               |
| :------------ | :------ | :--------------- | :--------------------------------------------------------------------------------- |
| `pattern`     | string  | `"TODO.*fix"`    | 要搜索的正则表达式模式                                                             |
| `path`        | string  | `"/path/to/dir"` | 可选的搜索文件或目录                                                               |
| `glob`        | string  | `"*.ts"`         | 可选的用于过滤文件的 glob 模式                                                     |
| `output_mode` | string  | `"content"`      | `"content"`、`"files_with_matches"` 或 `"count"`。默认为 `"files_with_matches"` |
| `-i`          | boolean | `true`           | 不区分大小写的搜索                                                                 |
| `multiline`   | boolean | `false`          | 启用多行匹配                                                                       |

##### WebFetch

获取并处理网页内容。

| 字段     | 类型   | 示例                          | 描述                               |
| :------- | :----- | :---------------------------- | :--------------------------------- |
| `url`    | string | `"https://example.com/api"`   | 要获取内容的 URL                   |
| `prompt` | string | `"提取 API 端点"`             | 在获取的内容上运行的提示词         |

##### WebSearch

搜索网页。

| 字段              | 类型   | 示例                           | 描述                               |
| :---------------- | :----- | :----------------------------- | :--------------------------------- |
| `query`           | string | `"react hooks best practices"` | 搜索查询词                         |
| `allowed_domains` | array  | `["docs.example.com"]`         | 可选：仅包含来自这些域名的结果     |
| `blocked_domains` | array  | `["spam.example.com"]`         | 可选：排除来自这些域名的结果       |

##### Task

启动[子代理 (subagent)](/en/sub-agents)。

| 字段            | 类型   | 示例                       | 描述                               |
| :-------------- | :----- | :------------------------- | :--------------------------------- |
| `prompt`        | string | `"查找所有 API 端点"`      | 代理要执行的任务                   |
| `description`   | string | `"查找 API 端点"`          | 任务的简短描述                     |
| `subagent_type` | string | `"Explore"`                | 要使用的专用代理类型               |
| `model`         | string | `"sonnet"`                 | 可选的用于覆盖默认值的模型别名     |

#### PreToolUse 决策控制

`PreToolUse` hook 可以控制工具调用是否继续执行。与其他使用顶级 `decision` 字段的 hook 不同，PreToolUse 在 `hookSpecificOutput` 对象中返回其决策。这提供了更丰富的控制：三种结果（允许 allow、拒绝 deny 或询问 ask），以及在执行前修改工具输入的能力。

| 字段                       | 描述                                                                                                                              |
| :------------------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| `permissionDecision`       | `"allow"` 绕过权限系统，`"deny"` 阻止工具调用，`"ask"` 提示用户确认                                                              |
| `permissionDecisionReason` | 对于 `"allow"` 和 `"ask"`，向用户显示但不会发给 Claude。对于 `"deny"`，则向 Claude 显示                                          |
| `updatedInput`             | 在执行前修改工具的输入参数。结合 `"allow"` 进行自动批准，或结合 `"ask"` 向用户显示修改后的输入                                   |
| `additionalContext`        | 在工具执行前添加到 Claude 上下文的字符串                                                                                          |

```json  theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "我的理由",
    "updatedInput": {
      "field_to_modify": "新值"
    },
    "additionalContext": "当前环境：生产环境。请谨慎操作。"
  }
}
```

<Note>
  PreToolUse 以前使用顶级 `decision` 和 `reason` 字段，但这些字段对于此事件已弃用。请改用 `hookSpecificOutput.permissionDecision` 和 `hookSpecificOutput.permissionDecisionReason`。弃用的值 `"approve"` 和 `"block"` 分别映射到 `"allow"` 和 `"deny"`。PostToolUse 和 Stop 等其他事件将继续使用顶级 `decision` 和 `reason` 作为其当前格式。
</Note>

### PermissionRequest

当用户看到权限对话框时运行。
使用 [PermissionRequest 决策控制](#permissionrequest-decision-control) 代表用户允许或拒绝。

匹配工具名称，与 PreToolUse 的值相同。

#### PermissionRequest 输入

PermissionRequest 钩子接收 `tool_name` 和 `tool_input` 字段，与 PreToolUse 钩子类似，但没有 `tool_use_id`。可选的 `permission_suggestions` 数组包含用户通常在权限对话框中看到的"始终允许"选项。区别在于钩子触发时机：PermissionRequest 钩子在向用户显示权限对话框之前运行，而 PreToolUse 钩子无论权限状态如何都在工具执行前运行。

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PermissionRequest",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf node_modules",
    "description": "Remove node_modules directory"
  },
  "permission_suggestions": [
    { "type": "toolAlwaysAllow", "tool": "Bash" }
  ]
}
```

#### PermissionRequest 决策控制

`PermissionRequest` 钩子可以允许或拒绝权限请求。除了所有钩子都可用的 [JSON 输出字段](#json-output) 外，您的钩子脚本可以返回一个包含以下事件特定字段的 `decision` 对象：

| 字段                 | 描述                                                                                                           |
| :------------------- | :------------------------------------------------------------------------------------------------------------- |
| `behavior`           | `"allow"` 授予权限，`"deny"` 拒绝权限                                                                          |
| `updatedInput`       | 仅用于 `"allow"`：在执行前修改工具的输入参数                                                                   |
| `updatedPermissions` | 仅用于 `"allow"`：应用权限规则更新，相当于用户选择"始终允许"选项                                               |
| `message`            | 仅用于 `"deny"`：告诉 Claude 为什么拒绝权限                                                                    |
| `interrupt`          | 仅用于 `"deny"`：如果为 `true`，则停止 Claude                                                                  |

```json  theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": {
        "command": "npm run lint"
      }
    }
  }
}
```

### PostToolUse

在工具成功完成后立即运行。

匹配工具名称，与 PreToolUse 的值相同。

#### PostToolUse 输入

`PostToolUse` 钩子在工具已成功执行后触发。输入包括 `tool_input`（发送给工具的参数）和 `tool_response`（工具返回的结果）。两者的确切模式取决于工具。

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

#### PostToolUse 决策控制

`PostToolUse` 钩子可以在工具执行后向 Claude 提供反馈。除了所有钩子都可用的 [JSON 输出字段](#json-output) 外，您的钩子脚本可以返回以下事件特定字段：

| 字段                   | 描述                                                                                       |
| :--------------------- | :----------------------------------------------------------------------------------------- |
| `decision`             | `"block"` 用 `reason` 提示 Claude。省略以允许操作继续                                      |
| `reason`               | 当 `decision` 为 `"block"` 时显示给 Claude 的解释                                          |
| `additionalContext`    | Claude 需要考虑的额外上下文                                                                |
| `updatedMCPToolOutput` | 仅用于 [MCP 工具](#match-mcp-tools)：用提供的值替换工具的输出                              |

```json  theme={null}
{
  "decision": "block",
  "reason": "决策解释",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "提供给 Claude 的额外信息"
  }
}
```

### PostToolUseFailure

在工具执行失败时运行。此事件在抛出错误或返回失败结果的工具调用时触发。用于记录失败、发送警报或向 Claude 提供纠正反馈。

匹配工具名称，与 PreToolUse 的值相同。

#### PostToolUseFailure 输入

PostToolUseFailure 钩子接收与 PostToolUse 相同的 `tool_name` 和 `tool_input` 字段，以及作为顶级字段的错误信息：

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PostToolUseFailure",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run test suite"
  },
  "tool_use_id": "toolu_01ABC123...",
  "error": "Command exited with non-zero status code 1",
  "is_interrupt": false
}
```

| 字段           | 描述                                                                     |
| :------------- | :----------------------------------------------------------------------- |
| `error`        | 描述出错内容的字符串                                                     |
| `is_interrupt` | 可选布尔值，指示失败是否由用户中断引起                                   |

#### PostToolUseFailure 决策控制

`PostToolUseFailure` 钩子可以在工具失败后向 Claude 提供上下文。除了所有钩子都可用的 [JSON 输出字段](#json-output) 外，您的钩子脚本可以返回以下事件特定字段：

| 字段                | 描述                                                   |
| :------------------ | :----------------------------------------------------- |
| `additionalContext` | Claude 需要与错误一起考虑的额外上下文                  |

```json  theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUseFailure",
    "additionalContext": "提供给 Claude 的关于失败的额外信息"
  }
}
```

### Notification

在 Claude Code 发送通知时运行。匹配通知类型：`permission_prompt`、`idle_prompt`、`auth_success`、`elicitation_dialog`。省略匹配器以运行所有通知类型的钩子。

使用单独的匹配器根据通知类型运行不同的处理程序。此配置在 Claude 需要权限批准时触发权限特定的警报脚本，在 Claude 空闲时触发不同的通知：

```json  theme={null}
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/permission-alert.sh"
          }
        ]
      },
      {
        "matcher": "idle_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/idle-notification.sh"
          }
        ]
      }
    ]
  }
}
```

#### Notification 输入

除了 [通用输入字段](#common-input-fields) 外，Notification 钩子接收包含通知文本的 `message`、可选的 `title` 和指示触发类型的 `notification_type`。

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Notification",
  "message": "Claude 需要您的权限才能使用 Bash",
  "title": "需要权限",
  "notification_type": "permission_prompt"
}
```

Notification 钩子无法阻止或修改通知。除了所有钩子都可用的 [JSON 输出字段](#json-output) 外，您可以返回 `additionalContext` 以向对话添加上下文：

| 字段                | 描述                      |
| :------------------ | :------------------------ |
| `additionalContext` | 添加到 Claude 上下文的字符串 |

### SubagentStart

在通过 Task 工具生成 Claude Code 子代理时运行。支持按代理类型名称（内置代理如 `Bash`、`Explore`、`Plan` 或 `.claude/agents/` 中的自定义代理名称）进行匹配。

#### SubagentStart 输入

除了 [通用输入字段](#common-input-fields) 外，SubagentStart 钩子接收包含子代理唯一标识符的 `agent_id` 和包含代理名称（内置代理如 `"Bash"`、`"Explore"`、`"Plan"` 或自定义代理名称）的 `agent_type`。

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SubagentStart",
  "agent_id": "agent-abc123",
  "agent_type": "Explore"
}
```

SubagentStart 钩子无法阻止子代理创建，但可以向子代理注入上下文。除了所有钩子都可用的 [JSON 输出字段](#json-output) 外，您可以返回：

| 字段                | 描述                            |
| :------------------ | :------------------------------------- |
| `additionalContext` | 添加到子代理上下文的字符串       |

```json  theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "遵循此任务的安全准则"
  }
}
```

### SubagentStop

在 Claude Code 子代理完成响应时运行。按代理类型匹配，与 SubagentStart 的值相同。

#### SubagentStop 输入

除了 [通用输入字段](#common-input-fields) 外，SubagentStop 钩子接收 `stop_hook_active`、`agent_id`、`agent_type` 和 `agent_transcript_path`。`agent_type` 字段是用于匹配器过滤的值。`transcript_path` 是会话主记录，而 `agent_transcript_path` 是存储在嵌套 `subagents/` 文件夹中的子代理自己的记录。

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../abc123.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SubagentStop",
  "stop_hook_active": false,
  "agent_id": "def456",
  "agent_type": "Explore",
  "agent_transcript_path": "~/.claude/projects/.../abc123/subagents/agent-def456.jsonl"
}
```

SubagentStop 钩子使用与 [Stop 钩子](#stop-decision-control) 相同的决策控制格式。

### Stop

在主 Claude Code 代理完成响应时运行。如果停止是由于用户中断引起的，则不会运行。

#### Stop 输入

除了 [通用输入字段](#common-input-fields) 外，Stop 钩子接收 `stop_hook_active`。当 Claude Code 已经由于 stop 钩子而继续运行时，此字段为 `true`。检查此值或处理记录以防止 Claude Code 无限运行。

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "stop_hook_active": true
}
```

#### Stop 决策控制

`Stop` 和 `SubagentStop` 钩子可以控制 Claude 是否继续。除了所有钩子都可用的 [JSON 输出字段](#json-output) 外，您的钩子脚本可以返回以下事件特定字段：

| 字段      | 描述                                                                |
| :--------- | :------------------------------------------------------------------------- |
| `decision` | `"block"` 阻止 Claude 停止。省略以允许 Claude 停止                       |
| `reason`   | 当 `decision` 为 `"block"` 时必需。告诉 Claude 为什么应该继续            |

```json  theme={null}
{
  "decision": "block",
  "reason": "当 Claude 被阻止停止时必须提供"
}
```

### PreCompact

在 Claude Code 即将运行压缩操作之前运行。

匹配器值指示压缩是手动触发还是自动触发：

| 匹配器   | 触发时机                                     |
| :------- | :------------------------------------------- |
| `manual` | `/compact`                                   |
| `auto`   | 上下文窗口满时自动压缩                       |

#### PreCompact 输入

除了 [通用输入字段](#common-input-fields) 外，PreCompact 钩子接收 `trigger` 和 `custom_instructions`。对于 `manual`，`custom_instructions` 包含用户传入 `/compact` 的内容。对于 `auto`，`custom_instructions` 为空。

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PreCompact",
  "trigger": "manual",
  "custom_instructions": ""
}
```

### SessionEnd

在 Claude Code 会话结束时运行。用于清理任务、记录会话统计或保存会话状态。支持按退出原因过滤的匹配器。

钩子输入中的 `reason` 字段指示会话结束的原因：

| 原因                          | 描述                                       |
| :---------------------------- | :----------------------------------------- |
| `clear`                       | 使用 `/clear` 命令清除会话                 |
| `logout`                      | 用户注销                                   |
| `prompt_input_exit`           | 用户在提示输入可见时退出                   |
| `bypass_permissions_disabled` | 绕过权限模式被禁用                         |
| `other`                       | 其他退出原因                               |

#### SessionEnd 输入

除了 [通用输入字段](#common-input-fields) 外，SessionEnd 钩子接收一个指示会话结束原因的 `reason` 字段。参见上面的 [原因表](#sessionend) 了解所有值。

```json  theme={null}
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SessionEnd",
  "reason": "other"
}
```

SessionEnd 钩子没有决策控制。它们无法阻止会话终止，但可以执行清理任务。

## 基于提示的钩子

除了 Bash 命令钩子（`type: "command"`）外，Claude Code 还支持基于提示的钩子（`type: "prompt"`），使用 LLM 评估是否允许或阻止操作。基于提示的钩子适用于以下事件：`PreToolUse`、`PostToolUse`、`PostToolUseFailure`、`PermissionRequest`、`UserPromptSubmit`、`Stop` 和 `SubagentStop`。

### 基于提示的钩子如何工作

基于提示的钩子不执行 Bash 命令，而是：

1. 将钩子输入和您的提示发送给 Claude 模型，默认为 Haiku
2. LLM 返回包含决策的结构化 JSON
3. Claude Code 自动处理决策

### 提示钩子配置

将 `type` 设置为 `"prompt"` 并提供 `prompt` 字符串而不是 `command`。使用 `$ARGUMENTS` 占位符将钩子的 JSON 输入数据注入到您的提示文本中。Claude Code 将组合提示和输入发送给快速的 Claude 模型，该模型返回 JSON 决策。

此 `Stop` 钩子要求 LLM 评估所有任务是否完成，然后才允许 Claude 结束：

```json  theme={null}
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "评估 Claude 是否应该停止：$ARGUMENTS。检查所有任务是否完成。"
          }
        ]
      }
    ]
  }
}
```

| 字段      | 必需 | 描述                                                                                                                                                         |
| :-------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `type`    | 是       | 必须是 `"prompt"`                                                                                                                                                   |
| `prompt`  | 是       | 发送给 LLM 的提示文本。使用 `$ARGUMENTS` 作为钩子输入 JSON 的占位符。如果 `$ARGUMENTS` 不存在，输入 JSON 将附加到提示末尾 |
| `model`   | 否       | 用于评估的模型。默认为快速模型                                                                                                                                      |
| `timeout` | 否       | 超时时间（秒）。默认：30                                                                                                                                            |

### 响应模式

LLM 必须返回包含以下内容的 JSON：

```json  theme={null}
{
  "ok": true | false,
  "reason": "决策解释"
}
```

| 字段     | 描述                                                |
| :------- | :--------------------------------------------------------- |
| `ok`     | `true` 允许操作，`false` 阻止操作                          |
| `reason` | 当 `ok` 为 `false` 时必需。显示给 Claude 的解释            |

### 示例：多条件 Stop 钩子

此 `Stop` 钩子使用详细提示在允许 Claude 停止前检查三个条件。如果 `"ok"` 为 `false`，Claude 将继续工作，并将提供的原因作为其下一条指令。`SubagentStop` 钩子使用相同格式评估 [子代理](/en/sub-agents) 是否应该停止：

```json  theme={null}
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "您正在评估 Claude 是否应该停止工作。上下文：$ARGUMENTS\n\n分析对话并确定是否：\n1. 所有用户请求的任务都已完成\n2. 需要处理任何错误\n3. 需要后续工作\n\n使用 JSON 响应：{\"ok\": true} 允许停止，或 {\"ok\": false, \"reason\": \"您的解释\"} 继续工作。",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## 基于代理的钩子

基于代理的钩子（`type: "agent"`）类似于基于提示的钩子，但具有多轮工具访问权限。不是单个 LLM 调用，代理钩子会生成一个子代理，该子代理可以读取文件、搜索代码和检查代码库以验证条件。代理钩子支持与基于提示的钩子相同的事件。

### 代理钩子如何工作

当代理钩子触发时：

1. Claude Code 使用您的提示和钩子的 JSON 输入生成子代理
2. 子代理可以使用 Read、Grep 和 Glob 等工具进行调查
3. 最多 50 轮后，子代理返回结构化的 `{ "ok": true/false }` 决策
4. Claude Code 以与提示钩子相同的方式处理决策

代理钩子适用于验证需要检查实际文件或测试输出，而不仅仅是评估钩子输入数据的情况。

### 代理钩子配置

将 `type` 设置为 `"agent"` 并提供 `prompt` 字符串。配置字段与 [提示钩子](#prompt-hook-configuration) 相同，默认超时更长：

| 字段      | 必需 | 描述                                                                                 |
| :-------- | :------- | :------------------------------------------------------------------------------------------ |
| `type`    | 是       | 必须是 `"agent"`                                                                           |
| `prompt`  | 是       | 描述要验证内容的提示。使用 `$ARGUMENTS` 作为钩子输入 JSON 的占位符 |
| `model`   | 否       | 使用的模型。默认为快速模型                                                                 |
| `timeout` | 否       | 超时时间（秒）。默认：60                                                                   |

响应模式与提示钩子相同：`{ "ok": true }` 允许或 `{ "ok": false, "reason": "..." }` 阻止。

此 `Stop` 钩子验证所有单元测试通过后才允许 Claude 结束：

```json  theme={null}
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "验证所有单元测试是否通过。运行测试套件并检查结果。$ARGUMENTS",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

## 在后台运行钩子

默认情况下，钩子会阻塞 Claude 的执行直到完成。对于部署、测试套件或外部 API 调用等长时间运行的任务，设置 `"async": true` 以在 Claude 继续工作时在后台运行钩子。异步钩子无法阻止或控制 Claude 的行为：响应字段如 `decision`、`permissionDecision` 和 `continue` 无效，因为它们本应控制的操作已经完成。

### 配置异步钩子

在命令钩子的配置中添加 `"async": true` 以在后台运行而不阻塞 Claude。此字段仅在 `type: "command"` 钩子上可用。

此钩子在每个 `Write` 工具调用后运行测试脚本。Claude 立即继续工作，而 `run-tests.sh` 执行最多 120 秒。当脚本完成时，其输出在下一次对话轮次中传递：

```json  theme={null}
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/run-tests.sh",
            "async": true,
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

`timeout` 字段设置后台进程的最大时间（秒）。如果未指定，异步钩子使用与同步钩子相同的 10 分钟默认值。

### 异步钩子如何执行

当异步钩子触发时，Claude Code 启动钩子进程并立即继续，无需等待完成。钩子通过 stdin 接收与同步钩子相同的 JSON 输入。

后台进程退出后，如果钩子生成的 JSON 响应包含 `systemMessage` 或 `additionalContext` 字段，该内容将在下一次对话轮次中作为上下文传递给 Claude。

### 示例：文件更改后运行测试

此钩子每当 Claude 写入文件时在后台启动测试套件，然后在测试完成后将结果报告给 Claude。将此脚本保存到项目中的 `.claude/hooks/run-tests-async.sh` 并使用 `chmod +x` 使其可执行：

```bash  theme={null}
#!/bin/bash
# run-tests-async.sh

# 从 stdin 读取钩子输入
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# 仅对源文件运行测试
if [[ "$FILE_PATH" != *.ts && "$FILE_PATH" != *.js ]]; then
  exit 0
fi

# 运行测试并通过 systemMessage 报告结果
RESULT=$(npm test 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "{\"systemMessage\": \"编辑 $FILE_PATH 后测试通过\"}"
else
  echo "{\"systemMessage\": \"编辑 $FILE_PATH 后测试失败：$RESULT\"}"
fi
```

然后将此配置添加到项目根目录的 `.claude/settings.json`。`async: true` 标志允许 Claude 在测试运行时继续工作：

```json  theme={null}
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-tests-async.sh",
            "async": true,
            "timeout": 300
          }
        ]
      }
    ]
  }
}
```

### 限制

与同步钩子相比，异步钩子有几个限制：

* 只有 `type: "command"` 钩子支持 `async`。基于提示的钩子无法异步运行。
* 异步钩子无法阻止工具调用或返回决策。当钩子完成时，触发操作已经执行。
* 钩子输出在下一次对话轮次中传递。如果会话空闲，响应将等待下一次用户交互。
* 每次执行创建一个单独的后台进程。同一异步钩子的多次触发不会去重。

## 安全注意事项

### 免责声明

钩子以您的系统用户的完整权限运行。

<Warning>
  钩子以您的完整用户权限执行 shell 命令。它们可以修改、删除或访问您的用户帐户可以访问的任何文件。在将钩子添加到配置之前，请审查和测试所有钩子命令。
</Warning>

### 安全最佳实践

编写钩子时请记住以下实践：

* **验证和清理输入**：切勿盲目信任输入数据
* **始终引用 shell 变量**：使用 `"$VAR"` 而不是 `$VAR`
* **阻止路径遍历**：检查文件路径中的 `..`
* **使用绝对路径**：为脚本指定完整路径，使用 `"$CLAUDE_PROJECT_DIR"` 作为项目根目录
* **跳过敏感文件**：避免 `.env`、`.git/`、密钥等

## 调试钩子

运行 `claude --debug` 以查看钩子执行详情，包括哪些钩子匹配、它们的退出代码和输出。使用 `Ctrl+O` 切换详细模式以在记录中查看钩子进度。

```
[DEBUG] Executing hooks for PostToolUse:Write
[DEBUG] Getting matching hook commands for PostToolUse with query: Write
[DEBUG] Found 1 hook matchers in settings
[DEBUG] Matched 1 hooks for query "Write"
[DEBUG] Found 1 hook commands to execute
[DEBUG] Executing hook command: <Your command> with timeout 600000ms
[DEBUG] Hook command completed with status 0: <Your stdout>
```

有关常见问题（如钩子未触发、无限 Stop 钩子循环或配置错误）的故障排除，请参阅指南中的 [限制和故障排除](/en/hooks-guide#limitations-and-troubleshooting)。