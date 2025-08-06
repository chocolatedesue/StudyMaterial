我来帮你梳理containerlab的基本用法。首先让我了解一下这个项目的结构和文档。

现在让我查看一些具体的命令行工具和控制功能：

现在让我查看一些链路控制和网络仿真的功能：

现在让我查看一些具体的示例和文档：

让我查看一些具体的实验示例：

现在让我查看一个简单的示例来了解基本结构：

让我查看一个更复杂的示例：

现在让我查看一些文档来了解更多功能：

基于我对containerlab代码库的分析，我来为你梳理containerlab的基本用法、拓扑定义和链路/节点控制功能：

## Containerlab 基本用法梳理

### 1. 核心概念

Containerlab是一个基于容器的网络实验室工具，主要用于构建和管理网络拓扑。它的核心组件包括：

- **节点(Nodes)**: 网络设备的容器化实例
- **链路(Links)**: 连接节点的虚拟网络连接
- **拓扑定义文件**: YAML格式的配置文件，定义整个实验室拓扑

### 2. 拓扑定义

#### 基本文件结构
拓扑定义文件使用 `*.clab.yml` 命名模式，基本结构如下：

````yaml path=lab-examples/srlceos01/srlceos01.clab.yml mode=EXCERPT
name: srlceos01

topology:
  nodes:
    srl:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:24.10
    ceos:
      kind: arista_ceos
      image: ceos:4.32.0F

  links:
    - endpoints: ["srl:ethernet-1/1", "ceos:eth1"]
````

#### 高级拓扑配置
更复杂的拓扑可以包含多种配置选项：

````yaml path=docs/manual/nodes.md mode=EXCERPT
topology:
  nodes:
    node1:  # node name
      kind: nokia_srlinux
      type: ixr-d2l
      image: ghcr.io/nokia/srlinux
      startup-config: /root/mylab/node1.cfg
      binds:
        - /usr/local/bin/gobgp:/root/gobgp
        - /root/files:/root/files:ro
      ports:
      - 80:8080
      - 55555:43555/udp
      user: test
      env:
        ENV1: VAL1
      cmd: /bin/bash script.sh
````

#### 支持的配置层级
- **defaults**: 全局默认配置
- **kinds**: 按设备类型的配置
- **groups**: 按组的配置  
- **nodes**: 具体节点配置

### 3. 基本命令操作

#### 部署实验室
```bash
# 部署指定拓扑文件
containerlab deploy -t mylab.clab.yml

# 部署当前目录下的拓扑文件
containerlab deploy

# 重新生成配置并部署
containerlab deploy -t mylab.clab.yml --reconfigure
```

#### 销毁实验室
```bash
# 销毁指定拓扑
containerlab destroy -t mylab.clab.yml

# 销毁并清理实验室目录
containerlab destroy -t mylab.clab.yml --cleanup

# 销毁所有实验室
containerlab destroy -a
```

#### 查看实验室状态
```bash
# 查看所有运行的实验室
containerlab inspect --all

# 查看特定实验室详情
containerlab inspect --name mylab

# 以JSON格式输出
containerlab inspect --name mylab -f json
```

### 4. 节点控制

#### 执行命令
```bash
# 在特定节点执行命令
containerlab exec -t mylab.clab.yml --label clab-node-name=srl1 --cmd 'show version'

# 在所有节点执行命令
containerlab exec -t mylab.clab.yml --cmd 'ip addr show'

# JSON格式输出
containerlab exec -t mylab.clab.yml --cmd 'show version' -f json
```

#### 直接访问节点
```bash
# 通过docker直接访问
docker exec -it clab-mylab-node1 bash

# 访问设备CLI
docker exec -it clab-mylab-srl sr_cli
```

### 5. 链路控制和网络仿真

Containerlab提供了强大的链路仿真功能，通过 `tools netem` 命令集实现：

#### 设置链路损伤
```bash
# 设置延迟和抖动
containerlab tools netem set -n clab-mylab-r1 -i eth1 --delay 5ms --jitter 1ms

# 设置丢包率
containerlab tools netem set -n clab-mylab-r1 -i eth1 --loss 10

# 设置带宽限制
containerlab tools netem set -n clab-mylab-r1 -i eth1 --rate 100

# 设置包损坏率
containerlab tools netem set -n clab-mylab-r1 -i eth1 --corruption 0.1

# 组合设置多种损伤
containerlab tools netem set -n clab-mylab-r1 -i eth1 --delay 10ms --loss 5 --rate 1000
```

#### 查看链路状态
```bash
# 查看节点的链路损伤设置
containerlab tools netem show -n clab-mylab-r1

# JSON格式输出
containerlab tools netem show -n clab-mylab-r1 -f json
```

#### 重置链路损伤
```bash
# 重置特定接口的损伤
containerlab tools netem reset -n clab-mylab-r1 -i eth1

# 清除所有损伤（设置为默认值）
containerlab tools netem set -n clab-mylab-r1 -i eth1
```

### 6. 接口和网络管理

#### 查看接口信息
```bash
# 查看所有节点的接口
containerlab inspect interfaces

# 查看特定节点的接口
containerlab inspect interfaces --node clab-mylab-node1
```

#### 支持的链路类型
- **veth**: 标准虚拟以太网对
- **bridge**: 桥接连接
- **host**: 主机网络连接
- **mgmt-net**: 管理网络连接

### 7. 实用功能

#### 生成拓扑图
```bash
# 生成拓扑图
containerlab graph -t mylab.clab.yml

# 生成不同格式的图
containerlab deploy -t mylab.clab.yml --graph
```

#### 配置管理
```bash
# 保存节点配置
containerlab save -t mylab.clab.yml

# 重新部署时保持配置
containerlab deploy -t mylab.clab.yml --reconfigure
```

### 8. 高级特性

#### 节点过滤
```bash
# 只部署特定节点
containerlab deploy -t mylab.clab.yml --node-filter node1,node2

# 只销毁特定节点
containerlab destroy -t mylab.clab.yml --node-filter node1
```

#### 多节点支持
Containerlab支持在多个主机上分布式部署拓扑，实现大规模网络仿真。

#### 模板化配置
支持使用Go模板语法创建动态拓扑配置，便于批量生成相似的网络拓扑。

这些功能使得containerlab成为一个功能强大的网络实验室工具，特别适合网络工程师进行协议测试、网络设计验证和教学演示。
