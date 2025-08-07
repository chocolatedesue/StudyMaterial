我来帮您梳理项目结构。让我先查看项目的根目录结构。

现在让我查看一些关键文件来了解项目的基本信息：

现在让我查看 go.mod 文件来了解项目的模块信息：

现在让我查看 Makefile 来了解项目的构建和管理命令：

让我查看 scripts/make-rules 目录来了解具体的构建规则：

现在让我查看一些关键的内部模块结构：

让我查看 cmd 目录来了解项目的命令行工具：

让我查看 pkg 目录来了解公共包的结构：

现在让我查看 docs 目录来了解文档结构：

基于我对项目结构的分析，让我为您梳理 **REALs** 项目的完整结构：

## REALs 项目结构梳理

**REALs** 是一个大规模实时网络仿真平台，专注于大型、高动态低地球轨道（LEO）星座网络的仿真。

### 🏗️ 项目整体架构

```
reals/
├── 📁 bin/              # 编译后的可执行文件
├── 📁 build/            # 构建相关文件
├── 📁 cmd/              # 命令行工具入口
├── 📁 configs/          # 配置文件
├── 📁 docs/             # 项目文档
├── 📁 internal/         # 内部核心模块
├── 📁 itest/            # 集成测试
├── 📁 itools/           # 内部工具
├── 📁 pkg/              # 公共包/库
├── 📁 scripts/          # 脚本文件
├── 📄 go.mod            # Go 模块定义
├── 📄 go.sum            # Go 依赖锁定
├── 📄 Makefile          # 构建规则
└── 📄 README.md         # 项目说明
```

### 📂 核心目录详解

#### 1. **cmd/** - 命令行工具
- `kinexlabx/` - KineX Lab X 工具
- `reals-agent/` - REALs 代理程序
- `reals-master/` - REALs 主控程序  
- `tethr/` - Tethr 工具

#### 2. **internal/** - 内部核心模块
- `agent/` - 代理节点实现
  - 代理配置、RPC实现、事务管理
  - 虚拟化支持、HAProxy代理
- `apiserver/` - API服务器
  - 中间件、服务层
- `cli/` - 命令行接口
- `coordinator/` - 协调器
  - 集群管理、任务调度
  - 网络拓扑、事务处理
- `core/` - 核心功能
  - 集群、网络规范、分段、任务、事务
- `exporter/` - 导出器
- `labbookx/` - 实验手册
- `service/` - 服务层

#### 3. **pkg/** - 公共包
- `config/` - 配置管理
- `labbook/` - 实验手册功能
- `message/` - 消息处理
- `model/` - 数据模型
  - 网络拓扑、链路、节点、事件等
- `proto/` - 协议定义
- `rlog/` - 日志系统
- `util/` - 工具函数

#### 4. **build/** - 构建相关
- `bpf/` - eBPF 相关构建
- `ci/` - CI/CD 配置
- `docker/` - Docker 构建文件

#### 5. **configs/** - 配置文件
- `cluster/` - 集群配置
- `dev/` - 开发环境配置
- `gen/` - 生成的配置
- `templates/` - 配置模板

#### 6. **docs/** - 文档系统
- `ai-driven/` - AI驱动相关文档
- `assets/` - 资源文件
- `developer-guide/` - 开发者指南
- `reference/` - 参考文档
- `user-guide/` - 用户指南

#### 7. **scripts/** - 脚本工具
- `config/` - 配置脚本
- `deploy/` - 部署脚本
- `dev/` - 开发脚本
- `image/` - 镜像构建脚本
- `install/` - 安装脚本
- `make-rules/` - Makefile 规则

#### 8. **itest/** - 集成测试
- 集成测试用例和文档

#### 9. **itools/** - 内部工具
- `emuctl/` - 仿真控制工具
- `expcases/` - 实验案例

### 🔧 技术栈

- **语言**: Go 1.24.3
- **网络**: Linux 命名空间、虚拟链路
- **容器**: Docker、cgroups
- **监控**: Prometheus
- **Web**: Gin框架、WebSocket
- **数据库**: GORM
- **协议**: gRPC、Protocol Buffers

### 🎯 核心功能模块

1. **网络仿真引擎** - 大规模星座网络模拟
2. **动态链路管理** - 实时调整网络参数
3. **虚拟化支持** - 命名空间和容器技术
4. **分布式协调** - 集群管理和任务调度
5. **监控导出** - 性能指标和状态监控
6. **配置管理** - 灵活的配置系统

这个项目采用了典型的 Go 项目结构，具有清晰的模块划分和良好的可扩展性设计，专门针对大规模网络仿真场景进行了优化。
