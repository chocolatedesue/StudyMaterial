让我搜索一下关于配置文件输入和拓扑加载的相关信息。

让我查看一些具体的配置文件示例：

现在让我查看一些具体的配置文件示例：

基于我对代码库的深入分析，我来为您详细介绍如何通过配置文件输入拓扑到REALS程序中：

## REALS支持的拓扑输入方式

### 1. YAML配置文件方式（推荐）

REALS提供了完整的YAML配置文件支持，这是最用户友好的方式：

#### 基础网络配置文件结构

````go path=pkg/labbook/network.go mode=EXCERPT
type NetworkConfig struct {
    Images   []Image    `yaml:"images,omitempty"`
    Nodes    []Node     `yaml:"nodes,omitempty"`
    Switches []L2Switch `yaml:"switches,omitempty"`
    Links    []Link     `yaml:"links,omitempty"`
}
````

#### 完整的YAML配置文件示例

```yaml
# network.yaml - 完整的网络拓扑配置文件
images:
  - type: "registry"
    repo: "ponedo/frr-ubuntu20"
    tag: "tiny"
    url: "harbor.fir.ac.cn"

nodes:
  - name: "router1"
    image: "ponedo/frr-ubuntu20:tiny"
    interfaces:
      - name: "eth0"
        mode: "single"        # single/multi/master/slave
        ip: ["192.168.1.1/24"]
        mac: "00:0e:0a:0b:0c:01"
      - name: "eth1"
        mode: "single"
        ip: ["192.168.2.1/24"]
        mac: "00:0e:0a:0b:0c:02"
    volumes:
      - host_path: "/tmp/router1"
        container_path: "/var/log"
        mode: "rw"

  - name: "router2"
    image: "ponedo/frr-ubuntu20:tiny"
    interfaces:
      - name: "eth0"
        mode: "single"
        ip: ["192.168.1.2/24"]
        mac: "00:0e:0a:0b:0c:03"
      - name: "eth1"
        mode: "single"
        ip: ["192.168.3.1/24"]
        mac: "00:0e:0a:0b:0c:04"

  - name: "router3"
    image: "ponedo/frr-ubuntu20:tiny"
    interfaces:
      - name: "eth0"
        mode: "single"
        ip: ["192.168.2.2/24"]
        mac: "00:0e:0a:0b:0c:05"
      - name: "eth1"
        mode: "single"
        ip: ["192.168.3.2/24"]
        mac: "00:0e:0a:0b:0c:06"

switches:
  - id: "switch1"
    properties:
      static_neigh: false    # 是否使用静态邻居表
      no_arp: false         # 是否禁用ARP

  - id: "switch2"
    properties:
      static_neigh: true
      no_arp: false

links:
  - id: "router1-router2"
    endpoints: ["router1:eth0", "router2:eth0"]
    switch: "switch1"

  - id: "router1-router3"
    endpoints: ["router1:eth1", "router3:eth0"]
    switch: "switch2"

  - id: "router2-router3"
    endpoints: ["router2:eth1", "router3:eth1"]
    switch: "switch2"
```

### 2. JSON拓扑文件方式

````go path=itools/pkg/exputil/topology.go mode=EXCERPT
type Topology struct {
    AdjNodeMap map[int]*Node `json:"adj_node_map"`
    
    NetNodeMap  map[int]model.NetNodeSpec     `json:"net_node_map"`
    VNicMap     map[int]model.VNicSpec        `json:"vnic_map"`
    LinkMap     map[string]model.LinkSpec     `json:"link_map"`
    L2DomainMap map[string]model.L2DomainSpec `json:"l2_domain_map"`
}
````

#### JSON拓扑文件示例

```json
{
  "adj_node_map": {
    "1": {
      "id": 1,
      "name": "node1",
      "neighbors": [2, 3]
    },
    "2": {
      "id": 2,
      "name": "node2", 
      "neighbors": [1, 3]
    },
    "3": {
      "id": 3,
      "name": "node3",
      "neighbors": [1, 2]
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
      "ip": ["192.168.1.1/24"],
      "mac": "00:0e:0a:0b:0c:01",
      "mode": "single"
    }
  },
  "link_map": {
    "link1-2": {
      "id": "link1-2",
      "vNIC_1_id": 1,
      "vNIC_2_id": 2,
      "l2_domain_id": "l2domain1"
    }
  },
  "l2_domain_map": {
    "l2domain1": {
      "id": "l2domain1",
      "static_neigh": false,
      "no_arp": false
    }
  }
}
```

## 如何输入配置文件到程序

### 1. 使用emuctl命令行工具

#### 方法1：通过LabBook方式（推荐）

````go path=cmd/kinexlabx/main.go mode=EXCERPT
func main() {
    flag.StringVar(&ip, "ip", "127.0.0.1", "ip address")
    flag.IntVar(&port, "port", 8080, "port")
    flag.StringVar(&labBookPath, "book", "", "lab book path")
    flag.BoolVar(&interactive, "i", false, "interactive mode")
    flag.Parse()

    client := apiclient.NewAPIClient(ip, strconv.Itoa(port))
    runner, err := labbookx.NewLabBookX(labBookPath, client)
````

**使用方式：**
```bash
# 1. 创建LabBook目录结构
mkdir -p my-experiment/network
cp network.yaml my-experiment/network/config.yaml

# 2. 运行实验
./kinexlabx -ip 172.20.64.6 -port 8080 -book my-experiment
```

#### 方法2：通过配置文件参数

````go path=itools/expcases/dynbps/cmd.go mode=EXCERPT
configFilePath := viper.GetString("cfg")
if configFilePath != "" {
    viper.SetConfigFile(configFilePath)
    if err := viper.ReadInConfig(); err != nil {
        fmt.Printf("❌ Failed to read config file %s: %v\n", configFilePath, err)
        return
    }
}
````

**使用方式：**
```bash
# 使用自定义配置文件
./emuctl dynbps setup --cfg my-config.yaml

# 或者使用命令行参数覆盖
./emuctl dynbps setup --ip 172.20.64.6 --port 8080 --gridx 10 --gridy 10
```

### 2. 配置文件加载流程

````go path=internal/labbookx/labbookx.go mode=EXCERPT
// 获取网络配置文件路径
networkConfigYamlPath := labbook.GetNetworkConfigYamlPath(base)
// 从YAML文件加载网络配置
networkConfig, err := labbook.NewNetworkConfigFromYamlFile(networkConfigYamlPath)
if err != nil {
    return nil, fmt.Errorf("failed to NewNetworkConfigFromYamlFile: %s", err)
}
````

### 3. 批量配置的目录结构

```
my-experiment/
├── network/
│   └── config.yaml          # 网络拓扑配置文件
├── playbook.yaml           # 实验脚本配置
├── actions/                # 动作库
│   ├── link/
│   │   └── set-bandwidth.json
│   └── node/
│       └── start-service.json
├── queries/                # 查询库
│   └── system/
│       └── get-stats.json
├── monitors/               # 监控库
│   └── link/
│       └── record-latency.json
└── outputs/                # 输出目录（自动生成）
    └── run-20250806-120000/
        ├── logs/
        ├── metrics/
        └── capture.pcap
```

## 实际使用示例

### 示例1：简单三节点网络

```yaml
# simple-network.yaml
nodes:
  - name: "node1"
    image: "ponedo/frr-ubuntu20:tiny"
    interfaces:
      - name: "eth0"
        mode: "single"
        ip: ["10.0.1.1/24"]

  - name: "node2"
    image: "ponedo/frr-ubuntu20:tiny"
    interfaces:
      - name: "eth0"
        mode: "single"
        ip: ["10.0.1.2/24"]

  - name: "node3"
    image: "ponedo/frr-ubuntu20:tiny"
    interfaces:
      - name: "eth0"
        mode: "single"
        ip: ["10.0.1.3/24"]

switches:
  - id: "main-switch"
    properties:
      static_neigh: false
      no_arp: false

links:
  - id: "node1-node2"
    endpoints: ["node1:eth0", "node2:eth0"]
    switch: "main-switch"
  
  - id: "node2-node3"
    endpoints: ["node2:eth0", "node3:eth0"]
    switch: "main-switch"
  
  - id: "node1-node3"
    endpoints: ["node1:eth0", "node3:eth0"]
    switch: "main-switch"
```

### 示例2：大规模网格拓扑

```yaml
# grid-network.yaml
# 使用配置参数生成网格拓扑
topology:
  type: "grid"
  grid_x: 5
  grid_y: 5
  
nodes:
  template:
    image: "ponedo/frr-ubuntu20:tiny"
    interfaces:
      - name: "eth0"
        mode: "single"
        ip_template: "192.168.{x}.{y}/24"

switches:
  - id: "grid-switch"
    properties:
      static_neigh: true
      no_arp: false
```

### 示例3：使用命令行工具

```bash
# 1. 创建实验目录
mkdir my-network-experiment
cd my-network-experiment

# 2. 创建网络配置
mkdir network
cat > network/config.yaml << EOF
nodes:
  - name: "router1"
    image: "ponedo/frr-ubuntu20:tiny"
    interfaces:
      - name: "eth0"
        mode: "single"
        ip: ["192.168.1.1/24"]
# ... 其他配置
EOF

# 3. 运行实验
kinexlabx -ip 172.20.64.6 -port 8080 -book .

# 或者使用emuctl
emuctl temporal setup --cfg config.yaml
```

## 配置文件验证和错误处理

系统提供了完整的配置验证：

````go path=internal/labbookx/network.go mode=EXCERPT
// 验证端点是否存在
for _, endpoint := range link.EndPoints {
    vNicId, ok := endPoint2Id[endpoint]
    if !ok {
        return nil, fmt.Errorf("end_point %s not found", endpoint)
    }
    vNicIdList = append(vNicIdList, vNicId)
}
````

## 总结

**REALS支持多种拓扑输入方式：**

1. **YAML配置文件**（推荐）：用户友好，支持复杂拓扑
2. **JSON拓扑文件**：适合程序生成的拓扑
3. **命令行参数**：适合简单配置和参数覆盖
4. **LabBook方式**：完整的实验管理框架

**最佳实践：**
- 使用YAML配置文件定义网络拓扑
- 通过LabBook目录结构组织实验
- 使用命令行参数进行快速调试
- 利用配置模板生成大规模拓扑

这种设计使得REALS既支持简单的手工配置，也支持复杂的自动化实验管理。
