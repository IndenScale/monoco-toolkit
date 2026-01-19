# 配置与依赖

## 5.1 扩展配置

- **`monoco.executablePath`**
  - **类型**: String
  - **默认值**: `monoco`
  - **作用**: 指定 Monoco 可执行文件的路径。若未设置，将尝试在系统 PATH 中查找。

## 5.2 外部依赖

- **Monoco CLI**
  - **用途**: 核心业务逻辑执行（Lint, Update, Index）。
  - **要求**: 必须在系统 PATH 中可访问。

- **Node.js Runtime**
  - **用途**: 运行 Language Server。
