让我搜索一下所有action type的定义和实现。

让我继续搜索更多关于action type的信息：

现在让我搜索更多关于网络事件类型的信息：

基于我对代码库的深入分析，我现在可以为您完整枚举REALS中所有合法的action配置操作：

## REALS Action Type 完整枚举

### 1. 顶层Action类型（有限集合）

````go path=pkg/labbook/action.go mode=EXCERPT
type ActionType string

const (
    ActionTypeNetworkEvents     ActionType = "network-events"
    ActionTypeNetFuncEvents     ActionType = "netfunc-events"
    ActionTypeNetFuncExecOutput ActionType = "netfunc-exec-output"
)
````

**REALS只支持3种顶层Action类型：**

1. **`network-events`** - 网络事件操作
2. **`netfunc-events`** - 网络功能事件操作
3. **`netfunc-exec-output`** - 网络功能执行输出操作

### 2. network-events 支持的操作类型

````go path=pkg/labbook/events.go mode=EXCERPT
// 网络事件类型常量定义
const (
    // 网络链路创建事件
    NetworkEventTypeLinkCreate NetworkEventType = "network-link-create"
    // 网络链路属性设置事件
    NetworkEventTypeLinkAttrSet NetworkEventType = "network-link-attr-set"
    // 网络链路销毁事件
    NetworkEventTypeLinkDestroy NetworkEventType = "network-link-destroy"
    // 网络节点创建事件
    NetworkEventTypeNodeCreate NetworkEventType = "network-node-create"
    // 网络节点销毁事件
    NetworkEventTypeNodeDestroy NetworkEventType = "network-node-destroy"
    // 网络接口创建事件
    NetworkEventTypeInterfaceCreate NetworkEventType = "network-interface-create"
    // 网络接口销毁事件
    NetworkEventTypeInterfaceDestroy NetworkEventType = "network-interface-destroy"
)
````

**network-events支持7种操作：**

#### 2.1 链路操作
- **`network-link-create`** - 动态创建链路
- **`network-link-attr-set`** - 设置链路属性（带宽、延迟、丢包率）
- **`network-link-destroy`** - 销毁链路

#### 2.2 节点操作
- **`network-node-create`** - 动态创建网络节点
- **`network-node-destroy`** - 销毁网络节点

#### 2.3 接口操作
- **`network-interface-create`** - 创建网络接口
- **`network-interface-destroy`** - 销毁网络接口

### 3. netfunc-events 支持的操作类型

````go path=pkg/model/netfunc_event.go mode=EXCERPT
const (
    NET_FUNC_EVENT_TYPE_CREATE  string = "Create"
    NET_FUNC_EVENT_TYPE_DESTROY string = "Destroy"
    NET_FUNC_EVENT_TYPE_EXEC    string = "Exec"
)
````

**netfunc-events支持3种操作：**

- **`Create`** - 创建网络功能（容器节点）
- **`Destroy`** - 销毁网络功能
- **`Exec`** - 在节点中执行命令

### 4. 完整的配置操作示例

#### 4.1 network-events 配置示例

```yaml
# actions/network/link-bandwidth-change.yaml
- type: "network-link-attr-set"
  link_id: "router1-router2"
  link_properties:
    mode: "up"
    bandwidth: "100Mbps"
    delay: "10ms"
    loss: "0.1%"

# actions/network/create-dynamic-link.yaml
- type: "network-link-create"
  link_id: "dynamic-link-1"
  link_create_args:
    endpoints: ["node1:eth1", "node2:eth1"]
    switch: "dynamic-switch"
  link_properties:
    mode: "up"
    bandwidth: "1Gbps"
    delay: "5ms"
    loss: "0%"

# actions/network/destroy-link.yaml
- type: "network-link-destroy"
  link_id: "link-to-remove"

# actions/network/create-node.yaml
- type: "network-node-create"
  node_name: "dynamic-router"
  node_create_args:
    image: "ponedo/frr-ubuntu20:tiny"
    interfaces:
      - name: "eth0"
        mode: "single"
        ip: ["192.168.10.1/24"]

# actions/network/destroy-node.yaml
- type: "network-node-destroy"
  node_name: "node-to-remove"

# actions/network/create-interface.yaml
- type: "network-interface-create"
  node_name: "router1"
  intf_name: "eth2"
  interface_create_args:
    mode: "single"
    ip: ["192.168.20.1/24"]
    mac: "00:0e:0a:0b:0c:20"

# actions/network/destroy-interface.yaml
- type: "network-interface-destroy"
  node_name: "router1"
  intf_name: "eth2"
```

#### 4.2 netfunc-events 配置示例

```yaml
# actions/node/start-bgp-service.yaml
- net_func_name: "router1"
  type: "Exec"
  exec_args:
    key: "start-bgp"
    shellcodes:
      - "systemctl start bird"
      - "birdc configure"
    daemon: true
    output: "/var/log/bgp-start.log"
    timeout: 30

# actions/node/generate-traffic.yaml
- net_func_name: "client1"
  type: "Exec"
  exec_args:
    key: "iperf3-test"
    shellcodes:
      - "iperf3 -c 192.168.1.2 -t 60 -i 1 -J"
    daemon: false
    output: "/tmp/iperf3-results.json"
    timeout: 70

# actions/node/create-container.yaml
- net_func_name: "new-router"
  type: "Create"
  create_args:
    image: "ponedo/frr-ubuntu20:tiny"
    volumes:
      - host_path: "/tmp/router-config"
        container_path: "/etc/frr"
        mode: "rw"

# actions/node/destroy-container.yaml
- net_func_name: "old-router"
  type: "Destroy"
```

#### 4.3 netfunc-exec-output 配置示例

```yaml
# actions/query/get-routing-table.yaml
net_func_name: "router1"
type: "Exec"
exec_args:
  key: "get-routes"
  shellcodes:
    - "ip route show"
    - "birdc show route"
  daemon: false
  output: "/tmp/routing-table.log"
  timeout: 10

# actions/query/ping-test.yaml
net_func_name: "client1"
type: "Exec"
exec_args:
  key: "connectivity-test"
  shellcodes:
    - "ping -c 5 192.168.1.2"
  daemon: false
  output: "/tmp/ping-results.log"
  timeout: 15
```

### 5. 实验时间线中的Action使用

```yaml
# playbook.yaml
timeline:
  - at: 0
    description: "启动BGP服务"
    action:
      type: "netfunc-events"
      source: "actions/node/start-bgp-service.yaml"
  
  - at: 5000
    description: "调整链路带宽"
    action:
      type: "network-events"
      source: "actions/network/link-bandwidth-change.yaml"
      with:
        link_id: "router1-router2"
        bandwidth: "50Mbps"
  
  - at: 10000
    description: "开始流量测试"
    action:
      type: "netfunc-events"
      source: "actions/node/generate-traffic.yaml"
  
  - at: 30000
    description: "收集路由信息"
    action:
      type: "netfunc-exec-output"
      source: "actions/query/get-routing-table.yaml"
  
  - at: 45000
    description: "创建动态链路"
    action:
      type: "network-events"
      source: "actions/network/create-dynamic-link.yaml"
  
  - at: 60000
    description: "测试新链路连通性"
    action:
      type: "netfunc-exec-output"
      source: "actions/query/ping-test.yaml"
```

## 总结

**REALS Action Type 完整列表：**

### 顶层Action类型（3种）
1. **`network-events`** - 网络基础设施操作
2. **`netfunc-events`** - 节点功能操作
3. **`netfunc-exec-output`** - 节点查询操作

### 网络事件子类型（7种）
1. **`network-link-create`** - 创建链路
2. **`network-link-attr-set`** - 设置链路属性
3. **`network-link-destroy`** - 销毁链路
4. **`network-node-create`** - 创建节点
5. **`network-node-destroy`** - 销毁节点
6. **`network-interface-create`** - 创建接口
7. **`network-interface-destroy`** - 销毁接口

### 网络功能事件子类型（3种）
1. **`Create`** - 创建容器
2. **`Destroy`** - 销毁容器
3. **`Exec`** - 执行命令

这个有限集合涵盖了REALS支持的所有实验操作类型，为网络仿真实验提供了完整的动态控制能力。
