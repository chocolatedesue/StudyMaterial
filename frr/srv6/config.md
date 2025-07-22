我来详细梳理 SRv6 在 FRR 中的配置和实现。让我先查看相关的代码和配置：

现在让我查看更多关于 SRv6 策略和配置的信息：

基于对 FRR 中 SRv6 代码和配置的深入分析，我来详细梳理 SRv6 的配置和实现：

# FRR 中 SRv6 配置详解

## 1. SRv6 架构概述

SRv6 在 FRR 中的架构分为几个层次：
```
应用层 (BGP VPN, ISIS, OSPF6)
├── SRv6 策略层 (pathd)
├── SRv6 管理层 (zebra)
└── 内核层 (Linux Kernel)
```

## 2. 核心配置组件

### 2.1 必要配置项

| 配置项 | 层次 | 必要性 | 说明 |
|--------|------|--------|------|
| `segment-routing srv6` | 全局 | **必须** | 启用SRv6功能 |
| `locator <name>` | SRv6 | **必须** | 定义SRv6定位器 |
| `prefix <prefix>` | 定位器 | **必须** | 设置定位器前缀 |

### 2.2 重要配置项

| 配置项 | 层次 | 作用 | 默认值 |
|--------|------|------|--------|
| `block-len <bits>` | 定位器 | 块长度 | 40 |
| `node-len <bits>` | 定位器 | 节点长度 | 24 |
| `func-bits <bits>` | 定位器 | 功能位长度 | 16 |
| `behavior usid` | 定位器 | 启用uSID | 关闭 |
| `source-address <ipv6>` | 封装 | 封装源地址 | 自动 |

## 3. 配置文件示例

### 3.1 基本 SRv6 定位器配置

```frr
# 基本SRv6配置
hostname R1

# 接口配置
interface lo0
 ipv6 address 2001:db8:1::1/128
!
interface eth0
 ipv6 address 2001:db8:12::1/64
!

# SRv6基本配置
segment-routing
 srv6
  locators
   locator loc1
    prefix 2001:db8:1:1::/64
   !
  !
 !
!

# 启用IPv6转发
ipv6 forwarding
!
```

### 3.2 详细 SRv6 定位器配置

```frr
# 详细SRv6定位器配置
hostname PE1

# 接口配置
interface lo0
 description "Loopback for SRv6"
 ipv6 address 2001:db8:1::1/128
!
interface eth0
 description "Core Network Interface"
 ipv6 address 2001:db8:12::1/64
!

# SRv6配置
segment-routing
 srv6
  # 封装配置
  encapsulation
   source-address 2001:db8:1::1
  !
  
  # 定位器配置
  locators
   locator main-loc
    # 定位器前缀和结构
    prefix 2001:db8:1:1::/64 block-len 40 node-len 24 func-bits 16
    
    # 行为配置
    behavior usid
   !
   
   # 备用定位器
   locator backup-loc
    prefix 2001:db8:1:2::/64 func-bits 8
   !
  !
 !
!

# 启用转发
ipv6 forwarding
!
```

### 3.3 BGP SRv6 L3VPN 配置

```frr
# BGP SRv6 L3VPN PE配置
hostname PE1

# VRF配置
vrf customer-a
 vni 1000
!
vrf customer-b
 vni 2000
!

# 接口配置
interface lo0
 ipv6 address 2001:db8:1::1/128
!
interface eth0
 description "Core Network"
 ipv6 address 2001:db8:12::1/64
!
interface eth1
 description "Customer A"
 vrf customer-a
 ipv6 address 2001:db8:100::1/64
 ip address 192.168.1.1/24
!
interface eth2
 description "Customer B"
 vrf customer-b
 ipv6 address 2001:db8:200::1/64
 ip address 192.168.2.1/24
!

# SRv6配置
segment-routing
 srv6
  locators
   locator main
    prefix 2001:db8:1:1::/64 func-bits 16
   !
  !
 !
!

# 主BGP配置
router bgp 65001
 bgp router-id 1.1.1.1
 bgp log-neighbor-changes
 no bgp default ipv4-unicast
 
 # iBGP邻居
 neighbor 2001:db8:2::1 remote-as 65001
 neighbor 2001:db8:2::1 description "PE2"
 neighbor 2001:db8:2::1 update-source lo0
 
 # SRv6配置
 segment-routing srv6
  locator main
 !
 
 # IPv4 VPN地址族
 address-family ipv4 vpn
  neighbor 2001:db8:2::1 activate
  neighbor 2001:db8:2::1 send-community extended
 exit-address-family
 
 # IPv6 VPN地址族
 address-family ipv6 vpn
  neighbor 2001:db8:2::1 activate
  neighbor 2001:db8:2::1 send-community extended
 exit-address-family
!

# 客户A的BGP配置
router bgp 65001 vrf customer-a
 bgp router-id 1.1.1.1
 no bgp ebgp-requires-policy
 
 # IPv4地址族
 address-family ipv4 unicast
  # SRv6 SID配置
  sid vpn export auto
  
  # 路由目标
  rd vpn export 65001:100
  rt vpn both 65001:100
  
  # VPN导入导出
  import vpn
  export vpn
  
  # 重分发连接路由
  redistribute connected
  
  # 网络通告
  network 192.168.1.0/24
 exit-address-family
 
 # IPv6地址族
 address-family ipv6 unicast
  # SRv6 SID配置
  sid vpn export auto
  
  # 路由目标
  rd vpn export 65001:1100
  rt vpn both 65001:1100
  
  # VPN导入导出
  import vpn
  export vpn
  
  # 重分发连接路由
  redistribute connected
 exit-address-family
!

# 客户B的BGP配置
router bgp 65001 vrf customer-b
 bgp router-id 1.1.1.1
 no bgp ebgp-requires-policy
 
 address-family ipv4 unicast
  sid vpn export auto
  rd vpn export 65001:200
  rt vpn both 65001:200
  import vpn
  export vpn
  redistribute connected
  network 192.168.2.0/24
 exit-address-family
 
 address-family ipv6 unicast
  sid vpn export auto
  rd vpn export 65001:1200
  rt vpn both 65001:1200
  import vpn
  export vpn
  redistribute connected
 exit-address-family
!

# 启用转发
ip forwarding
ipv6 forwarding
!
```

### 3.4 ISIS SRv6 配置

```frr
# ISIS SRv6配置
hostname R1

# 接口配置
interface lo0
 ipv6 address 2001:db8:1::1/128
 ipv6 router isis CORE
 isis passive
!
interface eth0
 ipv6 address 2001:db8:12::1/64
 ipv6 router isis CORE
 isis network point-to-point
 isis hello-interval 3
 isis hello-multiplier 3
!

# SRv6配置
segment-routing
 srv6
  locators
   locator main
    prefix 2001:db8:1:1::/64 block-len 40 node-len 24 func-bits 16
   !
  !
 !
!

# ISIS配置
router isis CORE
 net 49.0001.0000.0000.0001.00
 is-type level-2-only
 
 # SRv6配置
 segment-routing srv6
  locator main
  # 最大段深度配置
  max-seg-left-msd 8
  max-end-pop-msd 8
  max-h-encaps-msd 8
  max-end-d-msd 8
 !
 
 # 地址族配置
 address-family ipv6 unicast
  multi-topology
 exit-address-family
!

# 启用转发
ipv6 forwarding
!
```

### 3.5 SRv6 TE 策略配置

```frr
# SRv6 TE策略配置 (使用pathd)
hostname Headend

# 接口配置
interface lo0
 ipv6 address 2001:db8:1::1/128
!

# SRv6配置
segment-routing
 srv6
  locators
   locator main
    prefix 2001:db8:1:1::/64
   !
  !
 !
!

# SR-TE策略配置
segment-routing
 traffic-eng
  # 策略1: 到PE2的低延迟路径
  policy color 100 endpoint 2001:db8:2::1
   name "Low-Latency-to-PE2"
   binding-sid 1000
   
   candidate-path preference 200 name "primary" explicit segment-list sl1
   candidate-path preference 100 name "backup" explicit segment-list sl2
  !
  
  # 策略2: 到PE3的高带宽路径
  policy color 200 endpoint 2001:db8:3::1
   name "High-Bandwidth-to-PE3"
   binding-sid 2000
   
   candidate-path preference 100 name "primary" explicit segment-list sl3
  !
  
  # 段列表定义
  segment-list sl1
   index 10 sid 2001:db8:2:1::100
   index 20 sid 2001:db8:2:2::100
  !
  
  segment-list sl2
   index 10 sid 2001:db8:3:1::100
   index 20 sid 2001:db8:2:2::100
  !
  
  segment-list sl3
   index 10 sid 2001:db8:4:1::100
   index 20 sid 2001:db8:3:2::100
  !
 !
!

# PCE配置 (可选)
segment-routing
 traffic-eng
  pce-config
   pce-addr 2001:db8:100::1
   pcc
    peer 2001:db8:100::1 port 4189
   !
  !
 !
!
```

### 3.6 完整生产环境配置

```frr
# 完整SRv6生产环境配置
hostname Core-PE-01

# VRF配置
vrf CUSTOMER-A
 vni 10000
!
vrf CUSTOMER-B
 vni 20000
!

# 接口配置
interface lo0
 description "SRv6 Loopback"
 ipv6 address 2001:db8:1::1/128
!
interface eth0
 description "Core Network P2P"
 ipv6 address 2001:db8:12::1/64
 ipv6 nd ra-interval 10
 no ipv6 nd suppress-ra
!
interface eth1
 description "Customer A Access"
 vrf CUSTOMER-A
 ipv6 address 2001:db8:100::1/64
 ip address 192.168.1.1/24
!
interface eth2
 description "Customer B Access"
 vrf CUSTOMER-B
 ipv6 address 2001:db8:200::1/64
 ip address 192.168.2.1/24
!

# SRv6全局配置
segment-routing
 srv6
  # 封装配置
  encapsulation
   source-address 2001:db8:1::1
  !
  
  # 主定位器
  locators
   locator MAIN
    prefix 2001:db8:1:1::/64 block-len 40 node-len 24 func-bits 16
    behavior usid
   !
   
   # 备用定位器
   locator BACKUP
    prefix 2001:db8:1:2::/64 block-len 40 node-len 24 func-bits 16
   !
  !
 !
!

# BGP主配置
router bgp 65001
 bgp router-id 1.1.1.1
 bgp log-neighbor-changes
 bgp deterministic-med
 no bgp default ipv4-unicast
 
 # 邻居组配置
 neighbor RR-CLIENTS peer-group
 neighbor RR-CLIENTS remote-as 65001
 neighbor RR-CLIENTS update-source lo0
 neighbor RR-CLIENTS send-community extended
 neighbor RR-CLIENTS soft-reconfiguration inbound
 
 # 路由反射器
 neighbor 2001:db8:10::1 peer-group RR-CLIENTS
 neighbor 2001:db8:10::1 description "Route Reflector"
 
 # 其他PE
 neighbor 2001:db8:2::1 peer-group RR-CLIENTS
 neighbor 2001:db8:2::1 description "PE2"
 neighbor 2001:db8:3::1 peer-group RR-CLIENTS
 neighbor 2001:db8:3::1 description "PE3"
 
 # SRv6配置
 segment-routing srv6
  locator MAIN
 !
 
 # IPv4 VPN地址族
 address-family ipv4 vpn
  neighbor RR-CLIENTS activate
  neighbor RR-CLIENTS route-reflector-client
 exit-address-family
 
 # IPv6 VPN地址族
 address-family ipv6 vpn
  neighbor RR-CLIENTS activate
  neighbor RR-CLIENTS route-reflector-client
 exit-address-family
 
 # L2VPN EVPN地址族
 address-family l2vpn evpn
  neighbor RR-CLIENTS activate
  neighbor RR-CLIENTS route-reflector-client
  advertise-all-vni
 exit-address-family
!

# 客户A VRF BGP配置
router bgp 65001 vrf CUSTOMER-A
 bgp router-id 1.1.1.1
 no bgp ebgp-requires-policy
 
 # 客户CE连接
 neighbor 192.168.1.2 remote-as 65100
 neighbor 192.168.1.2 description "Customer A CE"
 neighbor 192.168.1.2 timers 30 90
 
 # IPv4地址族
 address-family ipv4 unicast
  # SRv6 SID配置
  sid vpn export auto
  
  # 路由目标配置
  rd vpn export 65001:10000
  rt vpn import 65001:10000
  rt vpn export 65001:10000
  
  # VPN路由导入导出
  import vpn
  export vpn
  
  # 邻居激活
  neighbor 192.168.1.2 activate
  neighbor 192.168.1.2 soft-reconfiguration inbound
  neighbor 192.168.1.2 route-map CUSTOMER-A-IN in
  neighbor 192.168.1.2 route-map CUSTOMER-A-OUT out
  
  # 重分发和网络通告
  redistribute connected
  network 192.168.1.0/24
 exit-address-family
 
 # IPv6地址族
 address-family ipv6 unicast
  sid vpn export auto
  rd vpn export 65001:60000
  rt vpn import 65001:60000
  rt vpn export 65001:60000
  import vpn
  export vpn
  redistribute connected
 exit-address-family
!

# 客户B VRF BGP配置
router bgp 65001 vrf CUSTOMER-B
 bgp router-id 1.1.1.1
 no bgp ebgp-requires-policy
 
 neighbor 192.168.2.2 remote-as 65200
 neighbor 192.168.2.2 description "Customer B CE"
 
 address-family ipv4 unicast
  sid vpn export auto
  rd vpn export 65001:20000
  rt vpn import 65001:20000
  rt vpn export 65001:20000
  import vpn
  export vpn
  neighbor 192.168.2.2 activate
  redistribute connected
  network 192.168.2.0/24
 exit-address-family
 
 address-family ipv6 unicast
  sid vpn export auto
  rd vpn export 65001:70000
  rt vpn import 65001:70000
  rt vpn export 65001:70000
  import vpn
  export vpn
  redistribute connected
 exit-address-family
!

# ISIS配置 (可选，用于IGP)
router isis CORE
 net 49.0001.0000.0000.0001.00
 is-type level-2-only
 
 segment-routing srv6
  locator MAIN
  max-seg-left-msd 10
  max-end-pop-msd 10
  max-h-encaps-msd 10
  max-end-d-msd 10
 !
 
 address-family ipv6 unicast
  multi-topology
 exit-address-family
!

# 路由策略
route-map CUSTOMER-A-IN permit 10
 description "Accept customer A prefixes"
 match ip address prefix-list CUSTOMER-A-PREFIXES
 set local-preference 200
!

route-map CUSTOMER-A-OUT permit 10
 description "Advertise to customer A"
 match ip address prefix-list ADVERTISE-TO-CUSTOMER-A
!

# 前缀列表
ip prefix-list CUSTOMER-A-PREFIXES seq 10 permit 192.168.1.0/24
ip prefix-list ADVERTISE-TO-CUSTOMER-A seq 10 permit 0.0.0.0/0

# 启用转发
ip forwarding
ipv6 forwarding
!

# 日志配置
log file /var/log/frr/frr.log
log syslog informational
!
```

## 4. 配置验证命令

### 4.1 基本状态检查
```bash
# 查看SRv6状态
vtysh -c "show segment-routing srv6"

# 查看定位器
vtysh -c "show segment-routing srv6 locator"
vtysh -c "show segment-routing srv6 locator MAIN detail"

# 查看SID分配
vtysh -c "show segment-routing srv6 sid"
```

### 4.2 BGP SRv6 VPN检查
```bash
# 查看BGP SRv6配置
vtysh -c "show bgp segment-routing srv6"

# 查看VPN路由
vtysh -c "show bgp ipv4 vpn"
vtysh -c "show bgp ipv6 vpn"

# 查看特定VRF
vtysh -c "show bgp vrf CUSTOMER-A ipv4"
vtysh -c "show bgp vrf CUSTOMER-A ipv6"
```

### 4.3 内核路由检查
```bash
# 查看内核SRv6路由
ip -6 route show table all | grep srv6

# 查看SRv6本地SID
ip sr show

# 查看SRv6策略
ip sr tunsrc show
```

### 4.4 详细诊断命令
```bash
# 查看SRv6统计
vtysh -c "show segment-routing srv6 statistics"

# 查看BGP邻居SRv6能力
vtysh -c "show bgp neighbors 2001:db8:2::1"

# 查看ISIS SRv6信息
vtysh -c "show isis segment-routing srv6"
```

## 5. 常见配置模板

### 5.1 最小SRv6配置模板
```frr
segment-routing
 srv6
  locators
   locator main
    prefix 2001:db8:1:1::/64
   !
  !
 !
ipv6 forwarding
!
```

### 5.2 标准BGP SRv6 L3VPN模板
```frr
segment-routing
 srv6
  locators
   locator main
    prefix 2001:db8:1:1::/64 func-bits 16
   !
  !
 !
router bgp 65001
 segment-routing srv6
  locator main
 !
 address-family ipv4 vpn
  neighbor <peer> activate
 exit-address-family
!
router bgp 65001 vrf <customer>
 address-family ipv4 unicast
  sid vpn export auto
  rd vpn export 65001:100
  rt vpn both 65001:100
  import vpn
  export vpn
 exit-address-family
!
```

### 5.3 高可用SRv6配置模板
```frr
segment-routing
 srv6
  encapsulation
   source-address 2001:db8:1::1
  !
  locators
   locator primary
    prefix 2001:db8:1:1::/64 block-len 40 node-len 24 func-bits 16
    behavior usid
   !
   locator backup
    prefix 2001:db8:1:2::/64 func-bits 16
   !
  !
 !
router bgp 65001
 segment-routing srv6
  locator primary
 !
!
```

## 6. 故障排除指南

### 6.1 常见问题
1. **定位器未生效**：检查前缀配置和内核支持
2. **SID分配失败**：检查func-bits长度和可用空间
3. **BGP邻居不支持SRv6**：确认邻居SRv6能力
4. **VPN路由未学习**：检查RT配置和SID导出

### 6.2 调试命令
```bash
# 启用调试
vtysh -c "debug segment-routing srv6"
vtysh -c "debug bgp vpn"
vtysh -c "debug zebra srv6"

# 查看日志
tail -f /var/log/frr/frr.log | grep -i srv6
```

这个详细的SRv6配置指南涵盖了从基本定位器配置到复杂的BGP SRv6 L3VPN部署的所有场景，可以作为SRv6网络部署的完整参考。