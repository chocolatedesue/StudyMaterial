让我详细查看 REALs 项目的配置生成工具和运行所需的配置。

现在让我查看一下开发环境的配置生成脚本：

基于我对 REALs 项目配置系统的深入分析，我来为你详细介绍运行所需的配置和配置生成工具。

## 🔧 REALs 项目配置完整指南

### 1. 📋 **核心配置文件概览**

REALs 项目需要以下几类配置文件才能运行：

#### A. 集群配置 (最重要)
- **主配置**: `configs/cluster/cluster-config.json` - 定义整个集群拓扑
- **模板配置**: `configs/cluster/cluster-config-template.json` - 配置模板

#### B. 服务配置
- **Master 配置**: `reals-master.yml` - 主控节点配置
- **Agent 配置**: `reals-agent.yml` - 代理节点配置

#### C. 容器编排配置
- **Docker Compose**: 各组件的容器部署配置

#### D. 监控配置
- **Prometheus**: 指标收集配置
- **Grafana**: 可视化仪表板配置
- **Loki**: 日志聚合配置

### 2. 🛠️ **配置生成工具**

REALs 提供了完善的配置生成工具链：

#### A. 生产环境配置生成
```bash
# 生成生产环境配置
make deploy.cluster-config-gen CLUSTER_CONFIG=configs/cluster/cluster-config.json
```

#### B. 开发环境配置生成
```bash
# 生成开发环境配置
make dev.cluster-config-gen
```

#### C. 手动配置生成
```bash
# 直接调用脚本
./scripts/deploy/cluster_config_gen.sh configs/cluster/cluster-config.json
./scripts/dev/cluster-config-gen.sh configs/cluster/cluster-config.json
```

### 3. 📝 **集群配置文件详解**

#### A. 主配置文件结构 (`cluster-config.json`)

````json path=configs/cluster/cluster-config-template.json mode=EXCERPT
{
  "global": {
    "dev_mode": false,
    "master_image": "harbor.fir.ac.cn/1iwenbin/reals-master:v1.0.0",
    "agent_image": "harbor.fir.ac.cn/1iwenbin/reals-agent:v1.0.0",
    "log_dir": "/home/cnic/reals/log",
    "driver_nfs_dir": "/mnt/reals-driver/nfs"
  },
  "master": {
    "ip": "172.20.64.6",
    "http_port": 8080,
    "rpc_port": 50051,
    "tcp_port": 8088
  },
  "agents": [
    {
      "id": 1,
      "ip": "172.20.64.6",
      "rpc_port": 50052,
      "phy_nic": "enp1s0",
      "semi_phy_nic": "enp8s0"
    }
  ]
}
````

#### B. 配置字段说明

**Global 全局配置**:
- `dev_mode`: 开发模式开关
- `master_image/agent_image`: Docker 镜像地址
- `log_dir`: 日志目录路径
- `driver_nfs_dir`: NFS 共享目录
- `user`: 运行用户
- `reals_dir`: 项目根目录

**Master 主节点配置**:
- `ip`: Master 节点 IP 地址
- `http_port`: HTTP API 端口 (默认 8080)
- `rpc_port`: gRPC 通信端口 (默认 50051)
- `tcp_port`: TCP 通信端口 (默认 8088)
- `keepalive`: 心跳间隔 (秒)

**Agents 代理节点配置**:
- `id`: Agent 唯一标识
- `ip`: Agent 节点 IP 地址
- `rpc_port`: gRPC 端口 (默认 50052)
- `phy_nic`: 物理网卡名称
- `semi_phy_nic`: 半物理网卡名称

**Monitor 监控配置** (可选):
- `prometheus_image`: Prometheus 镜像
- `grafana_image`: Grafana 镜像
- `loki_image`: Loki 镜像
- `node_exporter_image`: Node Exporter 镜像

### 4. 🚀 **快速配置和启动流程**

#### A. 首次部署 (生产环境)
```bash
# 1. 编辑集群配置
cp configs/cluster/cluster-config-template.json configs/cluster/cluster-config.json
vim configs/cluster/cluster-config.json  # 修改 IP、网卡等信息

# 2. 生成所有配置文件
make deploy.cluster-config-gen

# 3. 启动集群
make deploy.cluster-start

# 4. 启动监控 (可选)
make deploy.cluster-monitor-start
```

#### B. 开发环境快速启动
```bash
# 1. 修改开发配置
vim configs/cluster/cluster-config.json  # 设置本机 IP

# 2. 完整开发环境设置
make dev.cluster-setup

# 3. 启动开发环境
make dev.cluster-start

# 或者使用本地模式
make dev.start LOCAL_IP=127.0.0.1
```

#### C. 单机开发模式
```bash
# 1. 编译项目
make build

# 2. 生成开发配置
make dev.cluster-config-gen

# 3. 直接运行 (不使用容器)
./bin/reals-master --cfg configs/dev/master/reals-master.yml &
./bin/reals-agent --cfg configs/dev/agent/reals-agent.yml &
```

### 5. 📁 **配置文件生成位置**

#### A. 生产环境配置位置
```
/etc/reals/
├── master/
│   ├── reals-master.yml
│   └── docker-compose-master.yml
├── agent/
│   ├── reals-agent.yml
│   ├── docker-compose-agent.yml
│   └── docker-compose-node-exporter.yml
├── prometheus/
│   ├── prometheus.yml
│   └── docker-compose-prometheus.yml
└── grafana/
    ├── grafana.ini
    ├── docker-compose-grafana.yml
    └── provisioning/
```

#### B. 开发环境配置位置
```
configs/
├── dev/
│   ├── master/reals-master.yml
│   ├── agent/reals-agent.yml
│   ├── prometheus/
│   └── grafana/
└── gen/  # 临时生成目录
    ├── master/
    ├── agent-1/
    ├── prometheus/
    └── grafana/
```

### 6. 🔧 **配置自定义指南**

#### A. 修改网络配置
```bash
# 1. 获取本机网卡信息
ip addr show

# 2. 修改集群配置
vim configs/cluster/cluster-config.json
# 更新以下字段:
# - master.ip: 主节点 IP
# - agents[].ip: 各代理节点 IP  
# - agents[].phy_nic: 物理网卡名 (如 eth0, enp1s0)
# - agents[].semi_phy_nic: 半物理网卡名

# 3. 重新生成配置
make deploy.cluster-config-gen
```

#### B. 修改端口配置
```json
{
  "master": {
    "http_port": 8080,    // HTTP API 端口
    "rpc_port": 50051,    // gRPC 端口  
    "tcp_port": 8088      // TCP 通信端口
  },
  "agents": [
    {
      "rpc_port": 50052   // Agent gRPC 端口
    }
  ]
}
```

#### C. 修改镜像配置
```json
{
  "global": {
    "master_image": "your-registry/reals-master:v1.0.0",
    "agent_image": "your-registry/reals-agent:v1.0.0"
  },
  "monitor": {
    "prometheus_image": "prom/prometheus:latest",
    "grafana_image": "grafana/grafana:latest"
  }
}
```

### 7. 🔍 **配置验证和调试**

#### A. 配置文件验证
```bash
# 验证 JSON 格式
jq . configs/cluster/cluster-config.json

# 验证 YAML 格式
yq eval . configs/dev/master/reals-master.yml

# 检查生成的配置
ls -la /etc/reals/
ls -la configs/dev/
```

#### B. 网络连通性测试
```bash
# 测试端口连通性
telnet <master-ip> 8080
telnet <master-ip> 50051
telnet <agent-ip> 50052

# 测试网卡状态
ip link show <phy_nic>
ip link show <semi_phy_nic>
```

#### C. 服务状态检查
```bash
# 检查容器状态
docker ps
docker logs reals-master
docker logs reals-agent

# 检查进程状态
ps aux | grep reals
netstat -tulpn | grep -E "(8080|50051|50052)"
```

### 8. 📋 **配置模板说明**

项目提供了丰富的配置模板：

```` path=configs/templates mode=EXCERPT
configs/templates/
├── reals-master.yml      # Master 配置模板
├── reals-agent.yml       # Agent 配置模板  
├── prometheus-template.yml  # Prometheus 配置模板
├── loki-template.yml     # Loki 配置模板
└── grafana/              # Grafana 配置模板目录
    ├── grafana.ini
    └── provisioning/
````

### 9. 🚨 **常见配置问题**

#### A. IP 地址问题
```bash
# 问题: 配置的 IP 地址不正确
# 解决: 使用以下命令获取正确 IP
hostname -I | awk '{print $1}'
ip route get 8.8.8.8 | awk '{print $7}'
```

#### B. 网卡名称问题
```bash
# 问题: 网卡名称配置错误
# 解决: 查看可用网卡
ip link show
ls /sys/class/net/
```

#### C. 权限问题
```bash
# 问题: 配置文件权限不足
# 解决: 设置正确权限
sudo chown -R $USER:$USER configs/
sudo chmod -R 755 /etc/reals/
```

通过这套完整的配置系统，你可以轻松地部署和管理 REALs 集群。建议从单机开发模式开始，熟悉配置结构后再尝试分布式部署。
