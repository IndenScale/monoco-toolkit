# 智能执行 (Agent Actions)

该模块负责集成和执行标准作业程序 (SOP)。

## 3.1 动作发现 (Action Discovery)

-   **动作来源**
    -   **全局范围**: `~/.monoco/execution` 目录下的 SOP。
    -   **项目范围**: `.monoco/execution` 目录下的 SOP。
    -   **扫描机制**: 通过 LSP 请求 `monoco/getExecutionProfiles` 获取。

-   **展示界面**
    -   **TreeView**: 在 "Actions" 侧边栏树状列出所有可用动作。
    -   **模板查看**: 支持查看 Action 的原始 Prompt 模板 (`monoco.viewActionTemplate`)。

## 3.2 执行控制 (Execution Control)

-   **触发方式**
    -   **命令面板**: 运行 `Monoco: Run Action`。
    -   **右键菜单**: 在文件资源管理器或编辑器中右键触发。
    -   **TreeView**: 点击动作列表中的播放图标。

-   **上下文感知**
    -   **自动匹配**: 根据当前文件的元数据（Type, Stage）推荐相关 Action。
    -   **参数注入**: 自动将当前文件路径作为上下文传递给 Agent。

-   **交互式输入**
    -   **Instruction**: 执行前允许用户输入额外的自然语言指令（如“注意代码风格”）。
