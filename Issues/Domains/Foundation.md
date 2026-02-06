# Foundation

## 定义

Monoco 的基础层（Foundation），提供所有上层功能依赖的基石能力。它包含配置管理、依赖注入、资源加载、生命周期管理等框架级基础设施，是系统的"地基"。

## 职责

- **Configuration Management**: 配置加载、验证、合并与热更新
- **Dependency Injection**: IoC 容器、服务注册与解析
- **Resource Management**: Skills、Roles、Hooks 等核心资源的发现、加载与分发
- **Lifecycle Management**: 应用启动、关闭、信号处理
- **State Management**: 运行时状态持久化与同步
- **Git Integration**: 底层 Git 操作封装

## 边界

- **不负责**: 用户界面（CLI、IDE）、业务逻辑（Issue、Agent）、质量门禁
- **负责**: 为上述所有功能提供运行基础

## 原则

- **Stability First**: Kernel 变更需要严格的兼容性保证
- **Minimal Surface**: 暴露最小化的 API 接口
- **Pluggable**: 支持通过 Hooks 扩展，而非修改核心
