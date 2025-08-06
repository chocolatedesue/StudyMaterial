I'll help you understand the deployment methods within the reals project. Let me first explore the codebase to gather information about the deployment setup.

Let me look at the deployment-related directories and files to understand the deployment methods:

Now let me examine the key deployment files to understand the deployment methods:

Let me examine the deployment-related make rules:

Now let me examine the actual deployment scripts:

Let me also check the Docker-related files:

Now let me check the README to understand more about the deployment:

Let me also check if there are any development-related deployment files:

Let me check the development scripts directory:

Now let me check the build make rules to understand the build process:

Based on my analysis of the reals project, I can now provide you with a comprehensive overview of the deployment methods within the reals system.

## REALs 项目部署方式梳理

REALs (Real-time network Emulation At Large scale) 是一个大规模实时网络仿真平台，主要支持以下几种部署方式：

### 1. 🏗️ **构建方式**

#### 本地构建
- **Make 构建**: 使用 `make build` 进行本地编译
- **目标组件**: 
  - `reals-agent` - 代理节点
  - `reals-master` - 主控节点  
  - `tethr` - 网络工具
  - `kinexlabx` - 实验室扩展

#### 容器镜像构建
- **本地镜像**: `make image.build` (支持设置 IMAGE_TAG)
- **多平台镜像**: `make image.buildx.push` (构建并推送到远程仓库)
- **专用镜像**: `make image.build.labnode` (实验节点镜像)

### 2. 🚀 **部署模式**

#### A. 生产环境集群部署
使用 Docker Compose 进行分布式部署：

**核心组件**:
- **Master 节点**: 集群主控制器
- **Agent 节点**: 分布式代理节点
- **监控组件**: Prometheus + Grafana + Loki

**部署流程**:
```bash
# 1. 生成集群配置
make deploy.cluster-config-gen

# 2. 启动集群
make deploy.cluster-start

# 3. 启动监控
make deploy.cluster-monitor-start
```

#### B. 开发环境部署
支持本地开发和测试：

```bash
# 完整开发环境设置
make dev.cluster-setup

# 快速重新构建
make dev.cluster-remake

# 启动/停止开发集群
make dev.cluster-start
make dev.cluster-stop
```

### 3. 📋 **配置管理**

#### 集群配置文件
````json path=configs/cluster/cluster-config.json mode=EXCERPT
{
  "global": {
    "dev_mode": false,
    "master_image": "harbor.fir.ac.cn/1iwenbin/reals-master:v1.0.0",
    "agent_image": "harbor.fir.ac.cn/1iwenbin/reals-agent:v1.0.0",
    "log_dir": "/home/cnic/reals/log"
  },
  "master": {
    "ip": "172.20.64.6",
    "http_port": 8080,
    "rpc_port": 50051
  }
}
````

#### 配置生成机制
- **自动生成**: 基于模板和集群配置自动生成各节点配置
- **分发机制**: 通过 SSH 自动分发配置到各个节点
- **模板系统**: 支持 Prometheus、Grafana、Agent、Master 等组件模板

### 4. 🐳 **容器化部署**

#### Docker 镜像结构
- **reals-master**: 主控节点镜像
- **reals-agent**: 代理节点镜像 (需要特权模式)
- **labnode**: 实验节点镜像

#### 容器配置特点
- **网络模式**: 使用 `host` 网络模式
- **特权模式**: Agent 需要特权模式访问系统资源
- **卷挂载**: 
  - 配置文件挂载
  - 日志目录挂载
  - NFS 共享目录挂载
  - 系统目录挂载 (cgroup, proc, sys)

### 5. 📊 **监控部署**

#### 监控组件栈
- **Prometheus**: 指标收集和存储
- **Grafana**: 可视化仪表板
- **Loki**: 日志聚合
- **Node Exporter**: 节点指标导出
- **Promtail**: 日志收集

#### 监控配置
- 自动发现集群中的所有节点
- 动态生成 Prometheus 配置
- 预配置 Grafana 仪表板

### 6. 🔧 **部署工具链**

#### Make 命令体系
- **构建**: `build.mk` - 源码编译
- **镜像**: `image.mk` - 容器镜像构建
- **部署**: `deploy.mk` - 生产环境部署
- **开发**: `dev.mk` - 开发环境管理

#### 脚本工具
- **配置生成**: `cluster_config_gen.sh`
- **集群管理**: `cluster_start.sh`, `cluster_stop.sh`
- **环境设置**: `env-setup.sh`
- **代码分发**: `deliver-codes.sh`

### 7. 🌐 **网络架构**

#### 分布式架构
- **Master-Agent 模式**: 中心化控制，分布式执行
- **RPC 通信**: gRPC 协议进行节点间通信
- **网络隔离**: 基于 Linux namespace 的网络虚拟化

#### 部署拓扑
- Master 节点可以同时运行 Agent
- 支持跨主机的分布式部署
- 自动处理网络配置和防火墙规则

这套部署体系设计完善，支持从开发测试到生产环境的全生命周期部署需求，具有良好的可扩展性和可维护性。
