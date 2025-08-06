我来为您分类梳理REALs项目中的各种配置文件。

# REALs项目配置文件分类梳理

## 📁 配置文件总体分类

### 1. **核心服务配置** 🚀
用于配置REALs核心服务组件

#### 1.1 Master服务配置
- **`configs/templates/reals-master.yml`** - Master服务配置模板
- **`configs/dev/master/reals-master.yml`** - 开发环境Master配置
- **`configs/gen/master/`** - 生成的Master配置目录

````yaml path=configs/templates/reals-master.yml mode=EXCERPT
master:
    ip: 10.10.34.235              # Master IP地址
    http_port: 8080               # HTTP服务端口
    rpc_port: 50051               # RPC服务端口
    tcp_port: 8088                # TCP服务端口
    keepalive: 30                 # 心跳间隔
log:
    log_dir: /var/reals/log/master
    dev: false
````

#### 1.2 Agent服务配置
- **`configs/templates/reals-agent.yml`** - Agent服务配置模板
- **`configs/dev/agent/reals-agent.yml`** - 开发环境Agent配置
- **`configs/gen/agent-*/`** - 生成的Agent配置目录

````yaml path=configs/templates/reals-agent.yml mode=EXCERPT
agent:
    id: 1                         # Agent ID
    ip: 10.10.34.235              # Agent IP
    rpc_port: 50052               # RPC端口
    phy_nic: eth0                 # 物理网卡
    semi_phy_nic: eth1            # 半物理网卡
    work_dir: /var/reals/agent    # 工作目录
    master_ip: 10.10.34.235       # Master IP
    master_rpc_port: 50051        # Master RPC端口
log:
    log_dir: /var/reals/log/agent
    dev: false
````

### 2. **集群部署配置** 🏗️
用于集群环境的部署和管理

#### 2.1 集群配置文件
- **`configs/cluster/cluster-config-template.json`** - 集群配置模板
- **`configs/cluster/cluster-config.json`** - 实际集群配置
- **`scripts/config/cluster_config_template.json`** - 脚本用集群配置模板

````json path=configs/cluster/cluster-config-template.json mode=EXCERPT
{
  "global": {
    "dev_mode": false,
    "master_image": "harbor.fir.ac.cn/1iwenbin/reals-master:v1.0.0",
    "agent_image": "harbor.fir.ac.cn/1iwenbin/reals-agent:v1.0.0",
    "log_dir": "/home/cnic/reals/log",
    "user": "root"
  },
  "master": {
    "ip": "172.20.64.6",
    "http_port": 8080,
    "rpc_port": 50051
  },
  "agents": [
    {
      "id": 1,
      "ip": "172.20.64.6",
      "rpc_port": 50052,
      "phy_nic": "enp1s0"
    }
  ]
}
````

### 3. **监控系统配置** 📊
用于系统监控和日志管理

#### 3.1 Prometheus配置
- **`configs/templates/prometheus-template.yml`** - Prometheus配置模板
- **`configs/dev/prometheus/prometheus.yml`** - 开发环境Prometheus配置
- **`configs/dev/prometheus/docker-compose-prometheus.yml`** - Prometheus容器配置

#### 3.2 Grafana配置
- **`configs/templates/grafana/`** - Grafana配置模板目录
  - `grafana.ini` - Grafana主配置
  - `provisioning/` - 数据源和仪表板配置
  - `dashboards/` - 仪表板定义
- **`configs/dev/grafana/`** - 开发环境Grafana配置

#### 3.3 Loki配置
- **`configs/templates/loki-template.yml`** - Loki日志系统配置模板

````yaml path=configs/templates/loki-template.yml mode=EXCERPT
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096
  log_level: debug

common:
  instance_addr: 127.0.0.1
  path_prefix: /tmp/loki
  storage:
    filesystem:
      chunks_directory: /tmp/loki/chunks
      rules_directory: /tmp/loki/rules
````

### 4. **实验工具配置** 🧪
用于emuctl等实验工具

#### 4.1 Temporal实验配置
- **`itools/config.yaml`** - 当前打开的temporal实验配置

````yaml path=itools/config.yaml mode=EXCERPT
emulation:
    image: ponedo/frr-ubuntu20:tiny
    network_id: 1
    topology_id: 1
server:
    ip: localhost
    port: 8080
topology:
    file_path: topo.json
    grid_x: 3
    grid_y: 3
````

#### 4.2 实验案例配置
- **`itools/expcases/dualswitch/config.yaml`** - 双卫星切换实验配置
- **`itools/expcases/dynbps/config.yaml`** - 动态带宽缩放实验配置

### 5. **测试配置** 🧪
用于集成测试和单元测试

#### 5.1 集成测试配置
- **`itest/itests/config/test_config.json`** - 集成测试配置文件

````json path=itest/itests/config/test_config.json mode=EXCERPT
{
  "server": {
    "ip": "172.20.64.6",
    "port": "8080"
  },
  "test": {
    "base_dir": "/home/cnic/reals/itest/conf_test",
    "image": "ponedo/frr-ubuntu20:tiny"
  }
}
````

### 6. **容器编排配置** 🐳
用于Docker容器的编排和部署

#### 6.1 Docker Compose配置
- **`configs/dev/agent/docker-compose-node-exporter.yml`** - Node Exporter容器配置
- **`configs/dev/grafana/docker-compose-grafana.yml`** - Grafana容器配置
- **`configs/dev/prometheus/docker-compose-prometheus.yml`** - Prometheus容器配置

### 7. **实验室手册配置** 📚
用于LabBook实验管理

#### 7.1 网络配置
- **`network/config.yaml`** - 网络实验配置
- **`playbook.yaml`** - 实验剧本配置

## 📋 配置文件使用场景

### 开发环境
```
configs/dev/
├── agent/          # Agent开发配置
├── master/         # Master开发配置
├── prometheus/     # 监控开发配置
└── grafana/        # 可视化开发配置
```

### 生产环境
```
configs/templates/  # 配置模板
configs/cluster/    # 集群配置
configs/gen/        # 生成的配置
```

### 实验环境
```
itools/config.yaml                    # 实验工具配置
itools/expcases/*/config.yaml        # 各实验案例配置
itest/itests/config/test_config.json # 测试配置
```

## 🔧 配置文件管理

### 配置生成命令
```bash
# 生成temporal实验配置
emuctl temporal config-gen

# 生成集群配置
make deploy.cluster-config-gen

# 生成开发环境配置
make dev.cluster-config-gen
```

### 配置文件格式
- **YAML格式**: 服务配置、实验配置
- **JSON格式**: 集群配置、测试配置
- **INI格式**: Grafana配置

### 配置优先级
1. 命令行参数 (最高)
2. 环境变量
3. 配置文件
4. 默认值 (最低)

这个分类体系涵盖了REALs项目中所有类型的配置文件，从核心服务到监控系统，从开发环境到生产部署，为不同使用场景提供了完整的配置管理方案。
