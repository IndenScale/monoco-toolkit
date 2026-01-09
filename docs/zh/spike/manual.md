# Monoco Spike System 用户手册

Monoco Spike System 是一个用于管理临时研究性代码（Git Repo Spikes）的工具。它允许开发者方便地引入外部开源项目作为参考（Reference），同时保持主代码库的整洁。

## 1. 核心理念 (Core Concepts)

### 1.1 什么是 Spike？

在敏捷开发中，"Spike" 指的是为了降低技术风险或不确定性而进行的快速、临时性的实验或调研。

### 1.2 为什么需要 Spike System？

Monoco 鼓励 "站在巨人的肩膀上"（参考优秀的开源实现），但直接将外部代码库混入项目会导致：

- **仓库臃肿**: 提交无关的历史记录。
- **版权风险**: 意外混淆许可证。
- **干扰搜索**: 全局搜索时出现大量无关结果。

Spike System 通过 **物理隔离** 和 **自动化管理** 解决这些问题：

- **存放到 `.reference/`**: 默认将所有参考仓库下载到被 `.gitignore` 排除的目录。
- **配置化管理**: 在 `monoco.yaml` (或配置系统) 中记录仓库列表，而非直接提交代码。
- **按需同步**: 新成员只需运行 `sync` 即可拉取所有参考资料。

---

## 2. 命令行参考 (Command Reference)

### 2.1 初始化 (Init)

初始化 Spike 环境，主要是在项目根目录确保存放参考代码的目录已被添加到 `.gitignore` 中。

```bash
monoco spike init
```

### 2.2 添加仓库 (Add)

添加一个新的外部仓库到参考列表，并记录到配置中。

```bash
monoco spike add {url}
```

- **{url}**: Git 仓库地址 (支持 HTTPS 或 SSH)。
- 系统会自动推断仓库名称（例如 `https://github.com/foo/bar.git` -> `bar`）。
- **注意**: 添加后需运行 `monoco spike sync` 才会实际下载代码。

### 2.3 同步 (Sync)

下载或更新所有已配置的参考仓库。

```bash
monoco spike sync
```

- 如果仓库不存在，则执行 `git clone`。
- 如果仓库已存在，则执行 `git pull` (暂未实现自动 pull，目前主要保证存在)。
- 此命令是幂等的。

### 2.4 查看列表 (List)

列出所有已配置的参考仓库。

```bash
monoco spike list
```

### 2.5 移除 (Remove)

从配置中移除仓库，并可选择是否删除物理文件。

```bash
monoco spike remove {name} [--force]
```

- **{name}**: 仓库名称 (如 `bar`)。
- **--force, -f**: 强制删除物理目录而不询问。

---

## 3. 最佳实践 (Best Practices)

1. **只读引用 (Read-Only)**: `.reference/` 下的代码仅供阅读。**严禁**直接修改，也**严禁**在生产代码中直接 import 这些路径。
2. **及时清理**: 调研结束后，如果不再需要，应使用 `remove` 命令移除，减少磁盘占用。
3. **版权意识**: 在参考外部代码实现新的功能时，请务必遵守原项目的开源协议 (License)。
