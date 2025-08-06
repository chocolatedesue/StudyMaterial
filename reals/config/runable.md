我来帮你了解在当前项目中运行20x20网格拓扑需要准备什么配置文件。首先让我查看一下项目的结构和相关配置。

让我查看一下configs目录，这里应该包含了配置文件的模板和示例：

现在让我查看一下集群配置模板，这应该包含了拓扑配置的信息：

现在让我查看一下itools目录，这里可能包含了实验配置的工具：

让我查看一下expcases目录，这里应该包含了实验案例的配置：

让我查看一下这些实验案例的配置文件，了解拓扑配置的格式：

太好了！我发现dynbps案例正好是20x20的网格拓扑。让我查看一下itools的主配置文件：

现在让我搜索一下项目中关于拓扑配置的更多信息：

让我查看一下README文件，了解项目的整体结构：

现在让我查看一下itools的文档，了解如何使用工具：

基于我对项目的分析，我现在可以为你提供运行20x20网格拓扑所需的配置文件信息。

## 运行20x20网格拓扑需要准备的配置文件

根据项目结构分析，你需要准备以下几个配置文件：

### 1. 集群配置文件 (cluster-config.json)

这是最重要的配置文件，定义了集群的基础设置：

````json path=configs/cluster/cluster-config-template.json mode=EXCERPT
{
  "global": {
    "dev_mode": false,
    "master_image": "harbor.fir.ac.cn/1iwenbin/reals-master:v1.0.0",
    "agent_image": "harbor.fir.ac.cn/1iwenbin/reals-agent:v1.0.0",
    "log_dir": "/home/cnic/reals/log",
    "driver_nfs_dir": "/mnt/reals-driver/nfs",
    "user": "root",
    "reals_dir": "/home/cnic/reals"
  },
  "master": {
    "ip": "172.20.64.6",
    "http_port": 8080,
    "rpc_port": 50051,
    "tcp_port": 8088,
    "keepalive": 30
  },
  "agents": [...]
}
````

### 2. 实验配置文件 (config.yaml)

项目中已经有一个现成的20x20网格配置示例：

````yaml path=itools/expcases/dynbps/config.yaml mode=EXCERPT
ip: 172.20.64.6
port: 8080
gridx: 20
gridy: 20
event-num: 0
net-type: bpfnet # bpfnet, osnet
````

### 3. itools主配置文件

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
    grid_x: 20  # 修改为20
    grid_y: 20  # 修改为20
````

## 具体步骤

### 1. 复制并修改集群配置
```bash
cp configs/cluster/cluster-config-template.json configs/cluster/cluster-config.json
```
然后根据你的实际环境修改IP地址、端口等信息。

### 2. 使用现有的20x20配置
项目中的 `itools/expcases/dynbps/config.yaml` 已经是20x20的配置，可以直接使用或作为参考。

### 3. 修改itools配置
将 `itools/config.yaml` 中的 `grid_x` 和 `grid_y` 修改为20。

### 4. 运行实验
```bash
cd itools
# 使用dynbps案例（已经是20x20）
./bin/emuctl dynbps run

# 或者使用自定义配置
./bin/emuctl run --gridx=20 --gridy=20
```

## 关键配置参数说明

- **gridx/gridy**: 网格的X和Y维度，设置为20x20
- **net-type**: 网络类型，推荐使用 `bpfnet` 获得更好的性能
- **ip/port**: master服务器的地址和端口
- **image**: 容器镜像，用于网络节点
- **event-num**: 事件数量，0表示静态拓扑

项目已经提供了完整的20x20网格拓扑支持，你主要需要根据实际环境调整IP地址和路径配置即可。
