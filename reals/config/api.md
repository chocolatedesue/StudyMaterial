我来分析一下 REALS 系统暴露的交互接口，并举例说明可以进行哪些操作。

基于我对代码的深入分析，现在我来详细梳理 REALS 系统暴露的交互接口，并举例说明可以进行的操作：

# REALS 系统交互接口详解

## 1. API 接口概览

REALS 系统主要通过 HTTP REST API 和 WebSocket 接口提供服务，基础地址为：`http://localhost:8080/api/virtnet`

## 2. 核心 HTTP API 接口

### 2.1 网络拓扑管理

````go path=internal/apiserver/service/virtnet_service/virtnet_service.go mode=EXCERPT
func (vns *VirtNetService) InitRoutes(group *gin.RouterGroup) {
	// 网络拓扑管理
	group.POST("/topo/setup", vns.SetupNetTopology)
	group.POST("/topo/reset", vns.ResetNetTopology)
	group.POST("/topo/destroy", vns.DestroyNetTopology)
	
	// 网络管理
	group.POST("/network/setup", vns.SetupNetwork)
	group.POST("/network/destroy", vns.DestroyNetwork)
	
	// 镜像管理
	group.POST("/image/configure", vns.HandleImageConfigureRequest)
	group.POST("/image/destroy", vns.HandleImageDestroyRequest)
	group.POST("/image/cleanall", vns.HandleImageCleanAllRequest)
}
````

#### 示例：创建网络拓扑

```bash
# 创建网络拓扑
curl -X POST http://localhost:8080/api/virtnet/topo/setup \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "name": "test-topology",
    "net_nodes": [
      {
        "id": 1,
        "name": "node1"
      },
      {
        "id": 2,
        "name": "node2"
      }
    ],
    "vnics": [
      {
        "id": 1,
        "name": "eth0",
        "net_node_id": 1,
        "ip_list": ["192.168.1.1/24"],
        "mac": "00:11:22:33:44:55"
      }
    ],
    "links": [
      {
        "id": "link1",
        "vnic_1_id": 1,
        "vnic_2_id": 2,
        "l2_domain_id": "domain1"
      }
    ],
    "net_type": "bpfnet"
  }'
```

### 2.2 容器和网络功能管理

````go path=internal/apiserver/service/virtnet_service/virtnet_service.go mode=EXCERPT
// 网络功能事件
group.POST("/network/netfunc_event/batch_exec", vns.HandleNetFuncEvents)
group.POST("/network/netfunc_event/exec_output", vns.HandleNetFuncOutputEvent)

// 链路事件
group.POST("/network/link_event", vns.HandleLinkEvents)
group.POST("/netns/link_event", vns.HandleNetNsLinkEvents)

// 网络事件
group.POST("/network/network_event", vns.HandleNetworkEvents)
````

#### 示例：执行容器命令

```bash
# 批量执行容器命令
curl -X POST http://localhost:8080/api/virtnet/network/netfunc_event/batch_exec \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1,
    "netfunc_events": [
      {
        "netfunc_id": 1,
        "type": "exec",
        "exec_args": {
          "key": "ping-test",
          "shellcodes": ["ping -c 5 192.168.1.2"],
          "daemon": false,
          "timeout": 30
        }
      }
    ]
  }'
```

#### 示例：获取命令执行输出

```bash
# 执行命令并获取输出
curl -X POST http://localhost:8080/api/virtnet/network/netfunc_event/exec_output \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1,
    "netfunc_output_event": {
      "netfunc_id": 1,
      "type": "exec",
      "exec_args": {
        "key": "system-info",
        "shellcodes": ["uname -a", "free -h", "df -h"],
        "daemon": false,
        "output_path": "/tmp/system_info.txt",
        "timeout": 10
      }
    }
  }'
```

### 2.3 链路动态控制

#### 示例：动态修改链路属性

```bash
# 修改链路延迟和带宽
curl -X POST http://localhost:8080/api/virtnet/network/link_event \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1,
    "link_events": [
      {
        "link_id": "link1",
        "type": "attr_set",
        "properties": {
          "delay": "100ms",
          "bandwidth": "10Mbps",
          "loss": "1%"
        }
      }
    ]
  }'

# 禁用链路
curl -X POST http://localhost:8080/api/virtnet/network/link_event \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1,
    "link_events": [
      {
        "link_id": "link1",
        "type": "attr_set",
        "properties": {
          "mode": "down"
        }
      }
    ]
  }'
```

### 2.4 镜像管理

#### 示例：配置容器镜像

```bash
# 配置镜像
curl -X POST http://localhost:8080/api/virtnet/image/configure \
  -H "Content-Type: application/json" \
  -d '{
    "images": [
      {
        "type": "registry",
        "repo": "ponedo/frr-ubuntu20",
        "tag": "tiny",
        "url": "docker.io"
      },
      {
        "type": "docker_archive",
        "repo": "custom-router",
        "tag": "v1.0",
        "archive_path": "/path/to/image.tar"
      }
    ]
  }'
```

### 2.5 文件传输

````go path=internal/apiserver/service/virtnet_service/virtnet_service.go mode=EXCERPT
// 文件传输
group.POST("/network/vol_fetch", vns.HandleVolFetch)
````

#### 示例：从容器获取文件

```bash
# 获取容器内文件
curl -X POST http://localhost:8080/api/virtnet/network/vol_fetch \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1,
    "vol_fetch_entries": [
      {
        "netfunc_id": 1,
        "src_path": "/var/log/",
        "dst_path": "logs/"
      },
      {
        "netfunc_id": 2,
        "src_path": "/etc/config.conf",
        "dst_path": "configs/node2_config.conf"
      }
    ],
    "saved_path": "/tmp/experiment_data.zip"
  }'
```

## 3. WebSocket 接口

### 3.1 Web Terminal

````go path=internal/apiserver/service/virtnet_service/terminal.go mode=EXCERPT
func (vns *VirtNetService) HandleWebTerminal(c *gin.Context) {
	networkIdStr := c.Query("network_id")
	nodeIdStr := c.Query("node_id")
	cmdStr := c.Query("cmd")
	
	upgrader := websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool {
			return true
		},
	}
	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
}
````

#### 示例：连接 Web Terminal

```javascript
// JavaScript 客户端连接示例
const ws = new WebSocket('ws://localhost:8080/api/virtnet/ws/terminal?network_id=1&node_id=1');

ws.onopen = function(event) {
    console.log('Terminal connected');
    // 发送命令
    ws.send('ls -la\n');
};

ws.onmessage = function(event) {
    console.log('Terminal output:', event.data);
    // 显示终端输出
    document.getElementById('terminal').innerHTML += event.data;
};

ws.onclose = function(event) {
    console.log('Terminal disconnected');
};

// 发送用户输入
function sendCommand(command) {
    ws.send(command + '\n');
}
```

### 3.2 任务状态监控

````go path=internal/apiserver/service/virtnet_service/task_inspect.go mode=EXCERPT
func (vns *VirtNetService) InspectTaskStatus(c *gin.Context) {
	key := c.Param("key")
	taskMonitor, ok := vns.TaskMonitorMap[key]
	
	upgrader := websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool {
			return true
		},
	}
	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
}
````

#### 示例：监控任务状态

```javascript
// 监控任务执行状态
const taskKey = 'task-12345'; // 从任务创建响应中获取
const ws = new WebSocket(`ws://localhost:8080/api/virtnet/ws/task_inspect/${taskKey}`);

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Task status:', data);
    
    switch(data.state) {
        case 'running':
            console.log(`Progress: ${data.progress}%`);
            break;
        case 'done':
            console.log('Task completed successfully');
            break;
        case 'error':
            console.log('Task failed:', data.error);
            break;
    }
};
```

## 4. 高级功能接口

### 4.1 外部访问控制

```bash
# 启用外部访问
curl -X POST http://localhost:8080/api/virtnet/network/extac/enable \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1,
    "configs": [
      {
        "netfunc_id": 1,
        "port": 22,
        "protocol": "tcp"
      }
    ]
  }'

# 禁用外部访问
curl -X POST http://localhost:8080/api/virtnet/network/extac/disable \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1,
    "configs": [
      {
        "netfunc_id": 1,
        "port": 22,
        "protocol": "tcp"
      }
    ]
  }'
```

### 4.2 端口映射

```bash
# 启用端口映射
curl -X POST http://localhost:8080/api/virtnet/network/portmap/enable \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1,
    "configs": [
      {
        "netfunc_id": 1,
        "host_port": 8080,
        "container_port": 80,
        "protocol": "tcp"
      }
    ]
  }'
```

### 4.3 数据包捕获

```bash
# 开始数据包捕获
curl -X POST http://localhost:8080/api/virtnet/network/skbdump/start \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1,
    "capture_config": {
      "interface": "eth0",
      "filter": "tcp port 80",
      "max_packets": 1000
    }
  }'

# 停止数据包捕获
curl -X POST http://localhost:8080/api/virtnet/network/skbdump/stop \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1
  }'
```

### 4.4 Labbook 实验管理

```bash
# 初始化 Labbook 生成
curl -X POST http://localhost:8080/api/virtnet/lab_book/init \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1,
    "lab_book_key": "experiment-001"
  }'

# 获取 Labbook
curl -X POST http://localhost:8080/api/virtnet/lab_book/get \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": 1,
    "lab_book_key": "experiment-001",
    "path": "/path/to/save/labbook"
  }'
```

## 5. 健康检查和监控

### 5.1 系统健康检查

````go path=internal/apiserver/service/virtnet_service/health.go mode=EXCERPT
func (vns *VirtNetService) HandleHealthInspect(c *gin.Context) {
	running, total, err := GetClusterAgentsHealthStatus(vns.CoordinatorIP, vns.CoordinatorPort)
	
	response := gin.H{
		"running":   running,
		"total":     total,
		"timestamp": time.Now().Unix(),
	}
	c.JSON(http.StatusOK, response)
}
````

```bash
# 检查系统健康状态
curl -X GET http://localhost:8080/api/virtnet/health_inspect

# 响应示例
{
  "running": 3,
  "total": 3,
  "timestamp": 1704067200,
  "boot": true
}
```

## 6. 客户端 SDK 使用示例

### 6.1 Go 客户端

````go path=pkg/util/apiclient/client.go mode=EXCERPT
type APIClient struct {
	client *http.Client
	ip     string
	port   string
}

func NewAPIClient(ip string, port string) *APIClient {
	return &APIClient{
		client: &http.Client{},
		ip:     ip,
		port:   port,
	}
}

func (c *APIClient) SetupNetTopology(req *proto.NetTopoSetupRequest) error {
	return c.postRequest(fmt.Sprintf("http://%s:%s/api/virtnet/topo/setup", c.ip, c.port), req)
}
````

```go
// 使用示例
package main

import (
    "reals/pkg/util/apiclient"
    "reals/pkg/proto"
)

func main() {
    // 创建客户端
    client := apiclient.NewAPIClient("localhost", "8080")
    
    // 配置镜像
    imageReq := &proto.ImageConfigureRequest{
        Images: []model.ImageSpec{
            {
                Type: "registry",
                Repo: "ponedo/frr-ubuntu20",
                Tag:  "tiny",
                URL:  "docker.io",
            },
        },
    }
    err := client.ImageConfigure(imageReq)
    
    // 创建网络拓扑
    topoReq := &proto.NetTopoSetupRequest{
        NetTopoSpec: model.NetTopoSpec{
            Id:   1,
            Name: "test-network",
            // ... 其他配置
        },
    }
    err = client.SetupNetTopology(topoReq)
    
    // 执行容器命令
    execReq := &proto.NetFuncEventRequest{
        NetworkId: 1,
        NetFuncEvents: []model.NetFuncEvent{
            {
                NetFuncId: 1,
                Type:      "exec",
                ExecArgs: &model.NetFuncExecArgs{
                    ShellCodes: []string{"ping -c 5 192.168.1.2"},
                    Timeout:    30,
                },
            },
        },
    }
    err = client.ExecNetFuncEvent(execReq)
}
```

## 7. 可进行的主要操作总结

### 7.1 网络拓扑操作
- ✅ 创建、重置、销毁网络拓扑
- ✅ 动态添加/删除网络节点
- ✅ 配置虚拟网卡和链路

### 7.2 容器管理操作
- ✅ 配置和管理容器镜像
- ✅ 创建、启动、停止容器
- ✅ 执行容器内命令（一次性和守护进程模式）
- ✅ 获取命令执行输出

### 7.3 网络控制操作
- ✅ 动态修改链路属性（延迟、带宽、丢包率）
- ✅ 启用/禁用网络链路
- ✅ 配置外部访问控制
- ✅ 设置端口映射

### 7.4 交互操作
- ✅ Web Terminal 实时交互
- ✅ 文件传输（容器内外）
- ✅ 实时任务状态监控
- ✅ 数据包捕获和分析

### 7.5 实验管理操作
- ✅ Labbook 实验定义和执行
- ✅ 实验结果收集和导出
- ✅ 系统健康状态监控

REALS 系统提供了丰富的 API 接口，支持完整的网络仿真生命周期管理，从拓扑创建到实验执行，再到结果收集，都可以通过编程方式进行控制和自动化。
