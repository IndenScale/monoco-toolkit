# CLI 参考手册

Monoco CLI 是人类和 Agent 的主要交互接口。

## 全局选项

- `--root`: 设置 Issue 的根目录。
- `--json`: 以 JSON 格式输出结果（Agent 使用时推荐）。

## 命令集

### Issue 管理

`monoco issue [COMMAND]`

- `create`: 创建新 Issue (epic, feature, chore, fix)。
- `start`: 开始处理 Issue（自动创建分支或工作树）。
- `submit`: 提交审查。
- `close`: 关闭 Issue。
- `lint`: 检查 Issue 完整性。
- `list`: 列出所有 Issue。

### Spike (研究)

`monoco spike [COMMAND]`

- `add`: 添加参考仓库。
- `sync`: 同步参考数据。

### 文档国际化

`monoco i18n [COMMAND]`

- `scan`: 扫描缺失的翻译。
- `sync`: (计划中) 同步文档状态。

## 示例

```bash
# 创建一个新 Feature
monoco issue create feature -t "实现强大功能"

# 开始处理
monoco issue start FEAT-0001 --branch
```
