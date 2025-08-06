我来帮你了解如何上手开发和修改这个 REALs 项目。让我先查看一下项目的开发相关文档和配置。

现在让我查看一下项目的具体代码结构，了解主要组件：

让我查看一下开发相关的脚本：

现在让我查看一些关键的配置文件和示例：

让我查看一下测试相关的内容：

现在让我查看一下主要的入口文件，了解项目的启动方式：

基于我对 REALs 项目的深入分析，我来为你提供一个完整的开发上手指南：

## 🚀 REALs 项目开发上手指南

### 1. 📋 **项目概述**

REALs 是一个大规模实时网络仿真平台，主要用于模拟低地球轨道（LEO）星座网络。项目采用 **Master-Agent 分布式架构**：

- **reals-master**: 主控节点，负责任务调度和集群管理
- **reals-agent**: 代理节点，负责具体的网络仿真执行
- **tethr**: 网络工具组件
- **kinexlabx**: 实验室扩展组件

### 2. 🛠️ **开发环境准备**

#### A. 系统要求
- **操作系统**: Ubuntu 20.04 LTS 或更高版本
- **Go 版本**: 1.24.3 (项目使用较新版本)
- **Docker**: 20.10 或更高版本
- **权限**: 需要 root 权限进行网络操作

#### B. 基础环境安装

```bash
# 1. 克隆项目
git clone <repository-url>
cd reals

# 2. 安装 Go 环境
sudo bash scripts/install/install_go.sh

# 3. 安装 Docker
sudo bash scripts/install/install_docker.sh

# 4. 安装项目依赖
sudo bash scripts/install/install_deps.sh

# 5. 设置开发环境
make dev.env-setup
```

#### C. 项目依赖安装
```bash
# 安装 Go 模块依赖
go mod tidy

# 安装系统依赖和配置内核参数
sudo bash scripts/dev/env-setup.sh
```

### 3. 🏗️ **项目结构理解**

```` path=internal mode=EXCERPT
internal/
├── agent/          # Agent 节点核心逻辑
├── coordinator/    # Master 节点协调器
├── apiserver/      # HTTP API 服务
├── core/           # 核心数据结构和算法
├── exporter/       # 监控指标导出
└── service/        # 服务启动和管理
````

**核心组件说明**:
- **Agent**: 负责网络命名空间创建、链路模拟、流量控制
- **Coordinator**: 任务调度、集群管理、事务处理
- **Core**: 网络拓扑、任务分割、集群管理等核心算法
- **APIServer**: RESTful API 接口，支持 WebSocket

### 4. 🔧 **开发工作流**

#### A. 快速开始开发
```bash
# 1. 编译项目
make build

# 2. 生成开发配置
make dev.cluster-config-gen

# 3. 启动开发环境
make dev.cluster-start

# 4. 启动监控 (可选)
make dev.cluster-monitor-start
```

#### B. 开发模式运行
```bash
# 本地开发模式 (单机)
make dev.start LOCAL_IP=127.0.0.1

# 停止开发环境
make dev.stop
```

#### C. 代码修改后重新部署
```bash
# 重新编译和部署
make dev.cluster-remake

# 或者分步骤
make build                    # 编译
make dev.cluster-stop        # 停止服务
make dev.cluster-start       # 重启服务
```

### 5. 📝 **配置文件说明**

#### A. Master 配置 (`configs/dev/master/reals-master.yml`)
````yaml path=configs/dev/master/reals-master.yml mode=EXCERPT
master:
    ip: 172.20.64.6
    http_port: 8080      # HTTP API 端口
    rpc_port: 50051      # gRPC 端口
    tcp_port: 8088       # TCP 通信端口
    keepalive: 30
````

#### B. Agent 配置 (`configs/dev/agent/reals-agent.yml`)
````yaml path=configs/dev/agent/reals-agent.yml mode=EXCERPT
agent:
    id: 1
    ip: 172.20.64.6
    rpc_port: 50052
    phy_nic: enp1s0          # 物理网卡
    semi_phy_nic: vlan-ac    # 半物理网卡
    master_ip: 172.20.64.6   # Master 节点 IP
````

#### C. 集群配置 (`configs/cluster/cluster-config.json`)
这是最重要的配置文件，定义了整个集群的部署拓扑。

### 6. 🧪 **测试和调试**

#### A. 运行测试
```bash
# 运行单元测试
go test ./...

# 运行集成测试
cd itest
make test

# 运行特定测试
go test ./itest/itests/... -run TestName
```

#### B. 调试技巧
```bash
# 查看日志
tail -f /home/cnic/reals/log/master/reals-master.log
tail -f /home/cnic/reals/log/agent/reals-agent.log

# 查看容器状态
docker ps
docker logs reals-master
docker logs reals-agent

# 查看网络命名空间
ip netns list

# 监控系统资源
htop
iotop
```

### 7. 🔍 **开发重点关注点**

#### A. 网络仿真核心
- **命名空间管理**: `internal/agent/virt/`
- **链路模拟**: `internal/coordinator/vnet/`
- **拓扑管理**: `internal/coordinator/vtopo/`

#### B. 任务调度系统
- **任务管理**: `internal/coordinator/task*.go`
- **事务处理**: `internal/coordinator/cluster_transaction*.go`
- **Agent 管理**: `internal/coordinator/agent_node*.go`

#### C. API 接口
- **HTTP API**: `internal/apiserver/`
- **gRPC 接口**: `internal/*/rpc_impl.go`

### 8. 🚀 **常用开发命令**

```bash
# 完整开发环境设置 (首次)
make dev.cluster-setup

# 日常开发流程
make build                    # 编译
make dev.cluster-remake      # 重新部署
make dev.cluster-start       # 启动服务
make dev.cluster-stop        # 停止服务

# 镜像相关
make image.build IMAGE_TAG=dev-v1.0.0
make image.buildx.push IMAGE_TAG=dev-v1.0.0

# 监控相关
make dev.cluster-monitor-start
make dev.cluster-monitor-stop
```

### 9. 📊 **监控和观测**

开发环境会自动启动监控栈：
- **Prometheus**: http://localhost:9090 (指标收集)
- **Grafana**: http://localhost:3000 (可视化仪表板)
- **Node Exporter**: 端口 9100 (节点指标)
- **REALs Exporter**: 端口 9101 (应用指标)

### 10. 🐛 **常见问题解决**

#### A. 权限问题
```bash
# 确保有足够权限
sudo usermod -aG docker $USER
newgrp docker

# 检查网络权限
sudo sysctl net.ipv4.ip_forward=1
```

#### B. 端口冲突
```bash
# 检查端口占用
netstat -tulpn | grep :8080
netstat -tulpn | grep :50051

# 修改配置文件中的端口
```

#### C. 容器问题
```bash
# 清理容器
docker system prune -f

# 重新拉取镜像
docker pull harbor.fir.ac.cn/1iwenbin/reals-master:v1.0.0
```

### 11. 💡 **开发建议**

1. **从简单开始**: 先熟悉单机开发模式，再尝试分布式部署
2. **阅读代码**: 重点关注 `internal/service/` 下的启动逻辑
3. **理解架构**: 掌握 Master-Agent 通信机制和任务调度流程
4. **使用监控**: 利用 Prometheus 和 Grafana 观察系统行为
5. **增量开发**: 小步快跑，频繁测试验证

### 12. 📚 **进阶学习**

- 研究网络命名空间和 eBPF 技术
- 学习 gRPC 和 Protobuf 协议
- 了解容器网络和 Linux 网络栈
- 掌握分布式系统设计模式

这样你就可以开始 REALs 项目的开发了！建议先从简单的功能修改开始，逐步深入理解整个系统架构。
