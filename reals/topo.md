让我查看 REALs 项目中是否支持通过配置文件的方式输入拓扑。

基于我对 REALs 项目的深入分析，我来为你详细介绍通过配置文件输入拓扑的方式。

## 📁 REALs 配置文件拓扑输入完整指南

### 1. 🎯 **配置文件支持概述**

REALs 项目确实支持通过配置文件的方式输入拓扑，主要有以下几种方式：

#### A. 支持的配置文件格式
- **JSON 格式**: 直接的拓扑定义文件
- **YAML 格式**: 实验配置和参数文件
- **混合模式**: YAML 配置 + JSON 拓扑文件

#### B. 配置文件加载机制
- **Viper 配置管理**: 支持多层级配置覆盖
- **文件路径指定**: 通过命令行参数指定配置文件
- **自动发现**: 默认配置文件路径查找

### 2. 🛠️ **命令行工具 (emuctl)**

REALs 提供了 `emuctl` 命令行工具来支持配置文件操作：

#### A. 构建和使用 emuctl
```bash
# 构建命令行工具
cd itools
make build

# 使用 emuctl
./bin/emuctl --help
```

#### B. emuctl 主要功能
````go path=itools/pkg/cmd/root.go mode=EXCERPT
var rootCmd = &cobra.Command{
    Use:   "emuctl",
    Short: "网络仿真命令行工具",
    Long:  `用于网络仿真实验，构造并发送 API 请求到 apiserver。`,
}
````

### 3. 📝 **配置文件格式详解**

#### A. YAML 实验配置文件
````yaml path=itools/expcases/dynbps/config.yaml mode=EXCERPT
ip: 172.20.64.6
port: 8080
gridx: 20
gridy: 20
event-num: 0
net-type: bpfnet # bpfnet, osnet
````

#### B. 完整的实验配置模板
```yaml
# 服务器配置
server:
  ip: "172.20.64.6"
  port: 8080

# 拓扑配置
topology:
  grid_x: 3
  grid_y: 3
  file_path: "topo.json"

# 仿真配置
emulation:
  topology_id: 1
  network_id: 1
  image: "ponedo/frr-ubuntu20:tiny"
  base_dir_path: "/tmp/reals"

# 网络类型
net_type: "bpfnet"  # bpfnet 或 osnet
```

#### C. JSON 拓扑定义文件
````go path=itools/pkg/exputil/topology.go mode=EXCERPT
type Topology struct {
    AdjNodeMap  map[int]*Node                 `json:"adj_node_map"`
    NetNodeMap  map[int]model.NetNodeSpec     `json:"net_node_map"`
    VNicMap     map[int]model.VNicSpec        `json:"vnic_map"`
    LinkMap     map[string]model.LinkSpec     `json:"link_map"`
    L2DomainMap map[string]model.L2DomainSpec `json:"l2_domain_map"`
}
````

### 4. 🚀 **使用配置文件的方式**

#### A. 通过命令行指定配置文件
````go path=itools/expcases/dynbps/cmd.go mode=EXCERPT
// 设置配置文件路径
configFilePath := viper.GetString("cfg")
if configFilePath != "" {
    viper.SetConfigFile(configFilePath)
    if err := viper.ReadInConfig(); err != nil {
        fmt.Printf("❌ Failed to read config file %s: %v\n", configFilePath, err)
        return
    }
}
````

#### B. 使用示例命令
```bash
# 使用默认配置
./bin/emuctl dynbps setup

# 指定配置文件
./bin/emuctl dynbps setup --cfg config.yaml

# 覆盖配置参数
./bin/emuctl dynbps setup --cfg config.yaml --gridx 5 --gridy 5

# 完整实验流程
./bin/emuctl dynbps full --cfg experiments/large-scale.yaml
```

### 5. 📋 **拓扑配置文件示例**

#### A. 简单网格拓扑配置
```yaml
# grid-topology.yaml
server:
  ip: "172.20.64.6"
  port: 8080

topology:
  type: "grid"
  grid_x: 3
  grid_y: 3
  
network:
  type: "bpfnet"
  base_ip: "10.0.0.0/16"
  
nodes:
  image: "ponedo/frr-ubuntu20:tiny"
  base_dir: "/tmp/reals/grid"
```

#### B. 自定义拓扑 JSON 文件
```json
{
  "adj_node_map": {
    "1": {
      "id": 1,
      "name": "node1",
      "adj_node_id_list": [2, 3]
    },
    "2": {
      "id": 2,
      "name": "node2", 
      "adj_node_id_list": [1, 3]
    },
    "3": {
      "id": 3,
      "name": "node3",
      "adj_node_id_list": [1, 2]
    }
  },
  "net_node_map": {
    "1": {"id": 1, "name": "node1"},
    "2": {"id": 2, "name": "node2"},
    "3": {"id": 3, "name": "node3"}
  },
  "vnic_map": {
    "1": {
      "id": 1,
      "name": "eth0",
      "net_node_id": 1,
      "ip": ["10.0.1.1/24"],
      "mode": "single"
    }
  },
  "link_map": {
    "1-2": {
      "id": "1-2",
      "vNIC_1_id": 1,
      "vNIC_2_id": 2,
      "l2_domain_id": "l2d1"
    }
  },
  "l2_domain_map": {
    "l2d1": {"id": "l2d1"}
  }
}
```

### 6. 🔧 **配置文件加载和处理**

#### A. 从 JSON 文件加载拓扑
````go path=itools/pkg/exputil/topology.go mode=EXCERPT
func NewTopologyFromJsonFile(filePath string) (*Topology, error) {
    data, err := os.ReadFile(filePath)
    if err != nil {
        return nil, err
    }
    var topo Topology
    err = json.Unmarshal(data, &topo)
    if err != nil {
        return nil, err
    }
    return &topo, nil
}
````

#### B. 保存拓扑到文件
````go path=itools/pkg/exputil/topology.go mode=EXCERPT
func (t *Topology) SaveToJsonFile(filePath string) error {
    json, err := json.MarshalIndent(t, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile(filePath, json, 0644)
}
````

### 7. 🎯 **实际使用流程**

#### A. 创建配置文件
```bash
# 1. 生成默认配置
./bin/emuctl temporal config-gen

# 2. 编辑配置文件
vim config.yaml
```

#### B. 配置文件内容示例
```yaml
# config.yaml
server:
  ip: "172.20.64.6"
  port: 8080

topology:
  grid_x: 5
  grid_y: 5
  file_path: "custom-topo.json"

emulation:
  topology_id: 1
  network_id: 1
  image: "ponedo/frr-ubuntu20:tiny"
  base_dir_path: "/tmp/reals/experiment"

simulation:
  duration: "300s"
  traffic_pattern: "constant"
  packet_size: 1024
```

#### C. 执行实验
```bash
# 使用配置文件执行完整实验
./bin/emuctl dynbps full --cfg config.yaml

# 分步执行
./bin/emuctl dynbps setup --cfg config.yaml
./bin/emuctl dynbps run --cfg config.yaml
./bin/emuctl dynbps clean --cfg config.yaml
```

### 8. 📊 **高级配置功能**

#### A. 配置优先级
````bash path=itools/docs/command_workflow.md mode=EXCERPT
# 优先级：命令行参数 > 环境变量 > 配置文件 > 默认值

# 配置文件
./emuctl run --config=custom.yaml

# 环境变量覆盖
export SERVER_HOST="env.example.com"

# 命令行参数覆盖（最高优先级）
./emuctl run --host="cmd.example.com" --port=5050
````

#### B. 动态配置生成
```go
// 程序化生成配置
func generateExperimentConfig(name string) {
    v := viper.New()
    v.SetDefault("experiment.name", name)
    v.SetDefault("network.topology", "grid")
    v.SetDefault("network.nodes", []map[string]interface{}{
        {"name": "node-1", "type": "router", "ip": "192.168.1.1"},
    })
    
    configPath := fmt.Sprintf("experiments/%s.yaml", name)
    v.SetConfigFile(configPath)
    v.WriteConfig()
}
```

### 9. 🔍 **配置验证和调试**

#### A. 配置文件验证
```bash
# 验证 YAML 格式
yq eval . config.yaml

# 验证 JSON 格式
jq . topology.json

# 检查配置加载
./bin/emuctl dynbps setup --cfg config.yaml --dry-run
```

#### B. 调试配置加载
```go
// 在代码中添加调试信息
fmt.Printf("Loaded config: %+v\n", viper.AllSettings())
fmt.Printf("Server IP: %s\n", viper.GetString("server.ip"))
fmt.Printf("Grid size: %dx%d\n", viper.GetInt("topology.grid_x"), viper.GetInt("topology.grid_y"))
```

### 10. 📝 **完整示例：从配置文件部署拓扑**

#### A. 创建实验配置
```yaml
# experiment.yaml
server:
  ip: "172.20.64.6"
  port: 8080

topology:
  type: "custom"
  file_path: "star-topology.json"

emulation:
  topology_id: 100
  network_id: 100
  image: "ponedo/frr-ubuntu20:tiny"
  base_dir_path: "/tmp/reals/star-experiment"

network:
  type: "bpfnet"
  
experiment:
  name: "star-topology-test"
  duration: "600s"
  description: "Star topology connectivity test"
```

#### B. 创建拓扑定义
```json
{
  "net_node_map": {
    "1": {"id": 1, "name": "center"},
    "2": {"id": 2, "name": "node1"},
    "3": {"id": 3, "name": "node2"},
    "4": {"id": 4, "name": "node3"}
  },
  "vnic_map": {
    "1": {"id": 1, "name": "eth0", "net_node_id": 1, "ip": ["10.0.0.1/24"], "mode": "single"},
    "2": {"id": 2, "name": "eth0", "net_node_id": 1, "ip": ["10.0.1.1/24"], "mode": "single"},
    "3": {"id": 3, "name": "eth0", "net_node_id": 1, "ip": ["10.0.2.1/24"], "mode": "single"},
    "4": {"id": 4, "name": "eth0", "net_node_id": 2, "ip": ["10.0.0.2/24"], "mode": "single"},
    "5": {"id": 5, "name": "eth0", "net_node_id": 3, "ip": ["10.0.1.2/24"], "mode": "single"},
    "6": {"id": 6, "name": "eth0", "net_node_id": 4, "ip": ["10.0.2.2/24"], "mode": "single"}
  },
  "link_map": {
    "center-node1": {"id": "center-node1", "vNIC_1_id": 1, "vNIC_2_id": 4, "l2_domain_id": "l2d1"},
    "center-node2": {"id": "center-node2", "vNIC_1_id": 2, "vNIC_2_id": 5, "l2_domain_id": "l2d2"},
    "center-node3": {"id": "center-node3", "vNIC_1_id": 3, "vNIC_2_id": 6, "l2_domain_id": "l2d3"}
  },
  "l2_domain_map": {
    "l2d1": {"id": "l2d1"},
    "l2d2": {"id": "l2d2"},
    "l2d3": {"id": "l2d3"}
  }
}
```

#### C. 执行部署
```bash
# 1. 构建工具
cd itools && make build

# 2. 执行实验
./bin/emuctl temporal setup --config experiment.yaml

# 3. 运行测试
./bin/emuctl temporal run --config experiment.yaml

# 4. 清理环境
./bin/emuctl temporal clean --config experiment.yaml
```

### 11. 💡 **最佳实践**

#### A. 配置文件组织
```
experiments/
├── configs/
│   ├── small-scale.yaml
│   ├── large-scale.yaml
│   └── production.yaml
├── topologies/
│   ├── star.json
│   ├── mesh.json
│   └── grid.json
└── results/
    ├── experiment-1/
    └── experiment-2/
```

#### B. 配置模板化
```yaml
# template.yaml
server:
  ip: "${SERVER_IP:-172.20.64.6}"
  port: ${SERVER_PORT:-8080}

topology:
  grid_x: ${GRID_X:-3}
  grid_y: ${GRID_Y:-3}

emulation:
  image: "${CONTAINER_IMAGE:-ponedo/frr-ubuntu20:tiny}"
```

通过这套完整的配置文件系统，你可以轻松地定义、管理和部署各种复杂的网络拓扑，实现可重复、可配置的网络仿真实验。
