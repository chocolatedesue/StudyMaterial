我来为您梳理emuctl工具的详细使用手册。

# emuctl 使用手册

## 概述

**emuctl** 是REALs项目的网络仿真命令行工具，用于构造并发送API请求到apiserver，支持多种网络仿真实验场景。

````go path=itools/pkg/cmd/root.go mode=EXCERPT
var rootCmd = &cobra.Command{
    Use:   "emuctl",
    Short: "网络仿真命令行工具",
    Long:  `用于网络仿真实验，构造并发送 API 请求到 apiserver。`,
}
````

## 安装和构建

### 构建emuctl

```bash
# 进入itools目录
cd itools

# 构建emuctl
make build

# 查看帮助
./bin/emuctl --help
```

## 命令结构

emuctl采用分层命令结构，主要包含以下实验模块：

```
emuctl
├── temporal      # 时序实验
├── dualswitch    # 双卫星切换实验  
└── dynbps        # 动态带宽缩放实验
```

## 1. 双卫星切换实验 (dualswitch)

### 实验简介
双卫星切换实验模拟卫星网络中的链路切换场景，验证仿真平台在处理分布式、需要同步执行的原子状态更新时的时序保真度。

### 网络拓扑
- **菱形拓扑**：A(用户) ↔ B(主卫星) ↔ D(用户)，A ↔ C(备卫星) ↔ D
- **初始路径**：A-B-D (RTT ~20ms)
- **备用路径**：A-C-D (RTT ~50ms)

### 命令用法

````bash path=itools/expcases/dualswitch/cmd.go mode=EXCERPT
# 查看帮助
emuctl dualswitch --help

# 设置实验网络
emuctl dualswitch setup [选项]

# 运行切换实验
emuctl dualswitch run [选项]

# 清理实验环境
emuctl dualswitch clean [选项]

# 完整实验流程
emuctl dualswitch full [选项]

# 查看实验描述
emuctl dualswitch description
````

### 配置选项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--ip` | 172.20.64.6 | API服务器IP地址 |
| `--port` | 8080 | API服务器端口 |
| `--gridx` | 3 | 网格X轴大小 |
| `--gridy` | 3 | 网格Y轴大小 |
| `--event-num` | 0 | 事件数量 |
| `--net-type` | bpfnet | 网络类型(bpfnet/osnet) |
| `--cfg` | "" | 配置文件路径 |

### 配置文件示例

````yaml path=itools/expcases/dualswitch/config.yaml mode=EXCERPT
ip: 172.20.64.6
port: 8080
gridx: 3
gridy: 3
event-num: 0
net-type: bpfnet
````

### 使用示例

```bash
# 使用默认配置运行完整实验
emuctl dualswitch full

# 使用自定义配置文件
emuctl dualswitch setup --cfg ./config.yaml

# 使用命令行参数覆盖配置
emuctl dualswitch run --ip 192.168.1.100 --port 9090 --gridx 5 --gridy 5

# 分步执行实验
emuctl dualswitch setup
emuctl dualswitch run  
emuctl dualswitch clean
```

## 2. 动态带宽缩放实验 (dynbps)

### 实验简介
动态带宽缩放实验模拟网络中的带宽动态调整场景，测试网络在带宽变化时的性能表现。

### 命令用法

```bash
# 查看帮助
emuctl dynbps --help

# 设置实验网络
emuctl dynbps setup [选项]

# 运行带宽缩放实验
emuctl dynbps run [选项]

# 清理实验环境
emuctl dynbps clean [选项]

# 完整实验流程
emuctl dynbps full [选项]

# 查看实验描述
emuctl dynbps description
```

### 配置选项
与dualswitch实验相同的配置参数。

### 配置文件示例

````yaml path=itools/expcases/dynbps/config.yaml mode=EXCERPT
ip: 172.20.64.6
port: 8080
gridx: 20
gridy: 20
event-num: 0
net-type: bpfnet # bpfnet, osnet
````

### 使用示例

```bash
# 大规模网格拓扑实验
emuctl dynbps setup --gridx 20 --gridy 20

# 使用配置文件运行
emuctl dynbps full --cfg ./dynbps_config.yaml
```

## 3. 时序实验 (temporal)

### 实验简介
时序实验用于测试网络仿真的时序精度和同步性能。

### 命令用法

````bash path=itools/pkg/temporal/cmd.go mode=EXCERPT
# 查看帮助
emuctl temporal --help

# 生成配置文件
emuctl temporal config-gen

# 设置网络
emuctl temporal setup

# 运行时序实验
emuctl temporal run

# 清理网络
emuctl temporal clean
````

### 配置选项

```bash
# 指定配置文件
emuctl temporal --config ./config.yaml
```

## 配置管理

### 配置优先级
emuctl使用Viper进行配置管理，优先级如下：
1. **命令行参数** (最高优先级)
2. **环境变量**
3. **配置文件**
4. **默认值** (最低优先级)

### 环境变量设置

```bash
# 设置服务器地址
export SERVER_IP="192.168.1.100"
export SERVER_PORT="9090"

# 设置网络类型
export NET_TYPE="osnet"
```

### 配置文件格式
支持YAML格式的配置文件，可以为不同实验创建专用配置。

## 实验工作流程

### 标准实验流程

1. **Setup阶段**：创建网络拓扑和网络实例
2. **Run阶段**：执行具体的实验逻辑
3. **Clean阶段**：清理网络资源和拓扑

### 完整实验命令

```bash
# 方式1：分步执行
emuctl [experiment] setup
emuctl [experiment] run
emuctl [experiment] clean

# 方式2：一键执行
emuctl [experiment] full
```

## 网络类型支持

### BPF网络 (bpfnet)
- 高性能eBPF网络实现
- 适用于大规模仿真
- 默认网络类型

### OS网络 (osnet)
- 传统操作系统网络
- 兼容性更好
- 适用于小规模测试

## 故障排除

### 常见问题

1. **连接失败**
   ```bash
   # 检查API服务器状态
   curl http://172.20.64.6:8080/health
   
   # 使用正确的IP和端口
   emuctl dualswitch setup --ip 正确的IP --port 正确的端口
   ```

2. **配置文件错误**
   ```bash
   # 检查配置文件格式
   cat config.yaml
   
   # 使用绝对路径
   emuctl dualswitch setup --cfg /path/to/config.yaml
   ```

3. **权限问题**
   ```bash
   # 确保有执行权限
   chmod +x ./bin/emuctl
   ```

### 调试模式

```bash
# 查看详细输出
emuctl dualswitch setup -v

# 查看配置信息
emuctl dualswitch description
```

## 最佳实践

### 1. 配置管理
- 为不同环境创建专用配置文件
- 使用环境变量管理敏感信息
- 通过命令行参数进行临时覆盖

### 2. 实验执行
- 先运行小规模测试验证配置
- 使用`description`命令了解实验详情
- 实验完成后及时清理资源

### 3. 性能优化
- 大规模实验使用BPF网络类型
- 根据硬件资源调整网格大小
- 监控系统资源使用情况

## 扩展开发

### 添加新实验

1. 在`itools/expcases/`下创建新实验目录
2. 实现实验逻辑和命令接口
3. 在`root.go`中注册新命令

````go path=itools/pkg/cmd/root.go mode=EXCERPT
func init() {
    rootCmd.AddCommand(temporal.GetCommand())
    rootCmd.AddCommand(dualswitch.GetCommand())
    rootCmd.AddCommand(dynbps.GetCommand())
    // 添加新实验命令
    // rootCmd.AddCommand(newexperiment.GetCommand())
}
````

这份使用手册涵盖了emuctl工具的主要功能和使用方法，可以帮助用户快速上手并有效使用该工具进行网络仿真实验。
