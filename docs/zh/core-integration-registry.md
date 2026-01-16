# Core Integration Registry

## 概述

Core Integration Registry 是 Monoco 与外部 Agent 环境交互的统一"地图"。它提供了一个集中式的注册表,用于管理与各种 Agent 框架(Cursor、Claude、Gemini、Qwen、Antigravity 等)的集成。

## 核心概念

### AgentIntegration

每个 Agent 框架的集成配置包含以下字段:

- **key**: 唯一标识符(如 `cursor`, `gemini`)
- **name**: 人类可读的框架名称
- **system_prompt_file**: 系统提示文件路径(相对于项目根目录)
- **skill_root_dir**: 技能目录路径(相对于项目根目录)
- **enabled**: 是否启用该集成(默认: `true`)

### 默认集成表

| Framework       | Key      | System Prompt File | Skill Root Dir    |
| :-------------- | :------- | :----------------- | :---------------- |
| **Cursor**      | `cursor` | `.cursorrules`     | `.cursor/skills/` |
| **Claude Code** | `claude` | `CLAUDE.md`        | `.claude/skills/` |
| **Gemini CLI**  | `gemini` | `GEMINI.md`        | `.gemini/skills/` |
| **Qwen Code**   | `qwen`   | `QWEN.md`          | `.qwen/skills/`   |
| **Antigravity** | `agent`  | `GEMINI.md`        | `.agent/skills/`  |

## 使用方式

### 1. 使用默认集成

```python
from monoco.core.integrations import get_integration, DEFAULT_INTEGRATIONS

# 获取特定框架的集成配置
cursor_integration = get_integration("cursor")
print(cursor_integration.system_prompt_file)  # .cursorrules

# 查看所有默认集成
for key, integration in DEFAULT_INTEGRATIONS.items():
    print(f"{integration.name}: {integration.system_prompt_file}")
```

### 2. 自动检测项目中的框架

```python
from pathlib import Path
from monoco.core.integrations import detect_frameworks

# 检测当前项目使用的框架
root = Path.cwd()
frameworks = detect_frameworks(root)
print(f"Detected frameworks: {frameworks}")
# 输出: ['cursor', 'gemini']
```

### 3. 获取活跃的集成

```python
from monoco.core.integrations import get_active_integrations

# 获取已启用且在项目中检测到的集成
active = get_active_integrations(root, auto_detect=True)

for key, integration in active.items():
    print(f"Active: {integration.name}")
```

### 4. 通过配置文件自定义集成

在 `.monoco/config.yaml` 中:

```yaml
agent:
  # 自定义集成配置
  integrations:
    # 覆盖默认的 Cursor 配置
    cursor:
      key: cursor
      name: "My Custom Cursor"
      system_prompt_file: "custom-rules.md"
      skill_root_dir: ".my-cursor/skills/"
      enabled: true

    # 添加新的自定义框架
    my_framework:
      key: my_framework
      name: "My Custom Framework"
      system_prompt_file: "MY_FRAMEWORK.md"
      skill_root_dir: ".my-framework/skills/"
      enabled: true

    # 禁用某个框架
    qwen:
      key: qwen
      name: "Qwen Code"
      system_prompt_file: "QWEN.md"
      skill_root_dir: ".qwen/skills/"
      enabled: false
```

### 5. 在代码中使用配置覆盖

```python
from monoco.core.config import get_config
from monoco.core.integrations import get_integration, get_all_integrations

# 加载配置
config = get_config()

# 获取集成(会自动应用配置覆盖)
cursor = get_integration("cursor", config.agent.integrations)

# 获取所有集成(包含配置覆盖)
all_integrations = get_all_integrations(config.agent.integrations)
```

## API 参考

### `get_integration(name, config_overrides=None)`

获取指定的 Agent 集成配置。

**参数:**

- `name` (str): 框架标识符
- `config_overrides` (Dict[str, AgentIntegration], optional): 用户配置覆盖

**返回:** `AgentIntegration | None`

### `get_all_integrations(config_overrides=None, enabled_only=True)`

获取所有可用的集成配置。

**参数:**

- `config_overrides` (Dict[str, AgentIntegration], optional): 用户配置覆盖
- `enabled_only` (bool): 是否只返回已启用的集成

**返回:** `Dict[str, AgentIntegration]`

### `detect_frameworks(root)`

自动检测项目中存在的框架。

**参数:**

- `root` (Path): 项目根目录

**返回:** `List[str]` - 检测到的框架标识符列表

### `get_active_integrations(root, config_overrides=None, auto_detect=True)`

获取活跃的集成(已启用且已检测到)。

**参数:**

- `root` (Path): 项目根目录
- `config_overrides` (Dict[str, AgentIntegration], optional): 用户配置覆盖
- `auto_detect` (bool): 是否启用自动检测

**返回:** `Dict[str, AgentIntegration]`

## 设计原则

1. **集中式管理**: 所有框架集成配置集中在一个注册表中
2. **配置优先**: 用户配置可以覆盖默认设置
3. **智能检测**: 自动识别项目中使用的框架
4. **可扩展性**: 轻松添加新框架支持

## 后续计划

- [ ] 在 `monoco sync` 命令中使用集成注册表替代硬编码
- [ ] 支持技能分发时使用集成注册表
- [ ] 提供 CLI 命令查看和管理集成配置
