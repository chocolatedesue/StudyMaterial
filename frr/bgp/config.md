基于之前的讨论标准，我来总结 BGP 的核心配置和对应的配置文件示例：

# BGP 核心配置总结与示例

## 1. 配置层次结构

BGP 配置分为多个层次：
```
全局配置 (router bgp)
├── 邻居配置 (neighbor)
├── 地址族配置 (address-family)
├── 路由映射 (route-map)
└── 策略配置 (prefix-list, as-path-list, community-list)
```

## 2. 核心配置项分类

### 2.1 必要配置项 (基本运行必需)

| 配置项 | 层次 | 必要性 | 说明 |
|--------|------|--------|------|
| `router bgp <AS>` | 全局 | **必须** | 启用BGP进程并指定AS号 |
| `bgp router-id` | 全局 | **必须** | 设置BGP路由器ID |
| `neighbor <ip> remote-as` | 邻居 | **必须** | 配置BGP邻居 |
| `neighbor <ip> activate` | 地址族 | **必须** | 在地址族中激活邻居 |

### 2.2 重要配置项 (生产环境推荐)

| 配置项 | 层次 | 作用 | 默认值 |
|--------|------|------|--------|
| `bgp log-neighbor-changes` | 全局 | 记录邻居变化 | 关闭 |
| `bgp bestpath as-path multipath-relax` | 全局 | ECMP优化 | 关闭 |
| `neighbor <ip> password` | 邻居 | MD5认证 | 无 |
| `neighbor <ip> timers` | 邻居 | Keepalive/Hold定时器 | 60/180 |
| `neighbor <ip> soft-reconfiguration inbound` | 邻居 | 软重配置 | 关闭 |
| `maximum-paths` | 地址族 | 最大路径数 | 1 |

### 2.3 高级配置项 (特殊需求)

| 配置项 | 层次 | 用途 | 场景 |
|--------|------|------|------|
| `neighbor <ip> route-reflector-client` | 邻居 | 路由反射器 | 大型网络 |
| `confederation` | 全局 | 联邦配置 | 超大AS |
| `neighbor <ip> allowas-in` | 邻居 | 允许AS环路 | 特殊拓扑 |
| `bgp graceful-restart` | 全局 | 优雅重启 | 高可用 |
| `neighbor <ip> bfd` | 邻居 | BFD快速检测 | 快速收敛 |

## 3. 配置文件示例

### 3.1 基本 eBGP 配置

```frr
# 基本eBGP配置 - 单邻居
hostname R1

# 接口配置
interface eth0
 ip address 10.1.1.1/30
 ipv6 address 2001:db8:1::1/64
!
interface lo0
 ip address 1.1.1.1/32
 ipv6 address 2001:db8:100::1/128
!

# BGP配置
router bgp 65001
 # 基本配置
 bgp router-id 1.1.1.1
 bgp log-neighbor-changes
 
 # IPv4邻居
 neighbor 10.1.1.2 remote-as 65002
 neighbor 10.1.1.2 description "eBGP to AS65002"
 neighbor 10.1.1.2 password MyBGPSecret
 
 # IPv6邻居
 neighbor 2001:db8:1::2 remote-as 65002
 neighbor 2001:db8:1::2 description "eBGP IPv6 to AS65002"
 
 # IPv4地址族
 address-family ipv4 unicast
  # 通告本地网络
  network 1.1.1.1/32
  network 192.168.1.0/24
  
  # 激活邻居
  neighbor 10.1.1.2 activate
  neighbor 10.1.1.2 soft-reconfiguration inbound
 exit-address-family
 
 # IPv6地址族
 address-family ipv6 unicast
  # 通告本地网络
  network 2001:db8:100::1/128
  network 2001:db8:200::/48
  
  # 激活邻居
  neighbor 2001:db8:1::2 activate
  neighbor 2001:db8:1::2 soft-reconfiguration inbound
 exit-address-family
!
```

### 3.2 iBGP 配置 (路由反射器)

```frr
# iBGP路由反射器配置
hostname RR1

# Loopback接口
interface lo0
 ip address 1.1.1.1/32
 ipv6 address 2001:db8:rr::1/128
!

# BGP配置
router bgp 65001
 # 基本配置
 bgp router-id 1.1.1.1
 bgp log-neighbor-changes
 bgp cluster-id 1.1.1.1
 
 # 路由反射器客户端
 neighbor RR-CLIENTS peer-group
 neighbor RR-CLIENTS remote-as 65001
 neighbor RR-CLIENTS update-source lo0
 neighbor RR-CLIENTS route-reflector-client
 neighbor RR-CLIENTS next-hop-self
 
 # 客户端配置
 neighbor 2.2.2.2 peer-group RR-CLIENTS
 neighbor 2.2.2.2 description "RR Client - PE1"
 neighbor 3.3.3.3 peer-group RR-CLIENTS
 neighbor 3.3.3.3 description "RR Client - PE2"
 neighbor 4.4.4.4 peer-group RR-CLIENTS
 neighbor 4.4.4.4 description "RR Client - PE3"
 
 # 其他路由反射器 (非客户端)
 neighbor 5.5.5.5 remote-as 65001
 neighbor 5.5.5.5 description "RR Peer - RR2"
 neighbor 5.5.5.5 update-source lo0
 neighbor 5.5.5.5 next-hop-self
 
 # IPv4地址族
 address-family ipv4 unicast
  # 激活所有邻居
  neighbor RR-CLIENTS activate
  neighbor 5.5.5.5 activate
  
  # 最大路径数
  maximum-paths 4
  maximum-paths ibgp 4
 exit-address-family
 
 # VPNv4地址族 (MPLS VPN)
 address-family ipv4 vpn
  neighbor RR-CLIENTS activate
  neighbor 5.5.5.5 activate
 exit-address-family
!
```

### 3.3 多归属配置 (Multihoming)

```frr
# 多归属BGP配置
hostname Customer-Edge

# 接口配置
interface eth0
 description "Link to ISP1"
 ip address 203.0.113.2/30
!
interface eth1
 description "Link to ISP2"
 ip address 198.51.100.2/30
!
interface lo0
 ip address 192.168.100.1/32
!

# BGP配置
router bgp 65100
 bgp router-id 192.168.100.1
 bgp log-neighbor-changes
 
 # 最佳路径选择优化
 bgp bestpath as-path multipath-relax
 bgp bestpath compare-routerid
 
 # ISP1连接
 neighbor 203.0.113.1 remote-as 65001
 neighbor 203.0.113.1 description "Primary ISP"
 neighbor 203.0.113.1 password ISP1-Secret
 neighbor 203.0.113.1 timers 30 90
 
 # ISP2连接
 neighbor 198.51.100.1 remote-as 65002
 neighbor 198.51.100.1 description "Backup ISP"
 neighbor 198.51.100.1 password ISP2-Secret
 neighbor 198.51.100.1 timers 30 90
 
 # IPv4地址族
 address-family ipv4 unicast
  # 通告客户网络
  network 192.168.0.0/16
  
  # ISP1配置 (主链路)
  neighbor 203.0.113.1 activate
  neighbor 203.0.113.1 soft-reconfiguration inbound
  neighbor 203.0.113.1 route-map ISP1-IN in
  neighbor 203.0.113.1 route-map ISP1-OUT out
  
  # ISP2配置 (备份链路)
  neighbor 198.51.100.1 activate
  neighbor 198.51.100.1 soft-reconfiguration inbound
  neighbor 198.51.100.1 route-map ISP2-IN in
  neighbor 198.51.100.1 route-map ISP2-OUT out
  
  # 负载均衡
  maximum-paths 2
 exit-address-family
!

# 路由策略
# ISP1入方向 - 设置较高本地优先级
route-map ISP1-IN permit 10
 set local-preference 200
!

# ISP2入方向 - 设置较低本地优先级
route-map ISP2-IN permit 10
 set local-preference 100
!

# ISP1出方向 - 正常通告
route-map ISP1-OUT permit 10
 match ip address prefix-list CUSTOMER-PREFIXES
!

# ISP2出方向 - AS-PATH预置 (降低优先级)
route-map ISP2-OUT permit 10
 match ip address prefix-list CUSTOMER-PREFIXES
 set as-path prepend 65100 65100
!

# 前缀列表
ip prefix-list CUSTOMER-PREFIXES seq 10 permit 192.168.0.0/16
!
```

### 3.4 MPLS VPN PE 配置

```frr
# MPLS VPN PE路由器配置
hostname PE1

# VRF配置
vrf CUSTOMER-A
 vni 1000
!
vrf CUSTOMER-B
 vni 2000
!

# 接口配置
interface eth0
 description "P2P to P router"
 ip address 10.0.1.1/30
 mpls enable
!

# 客户接口
interface eth1
 description "Customer A"
 vrf CUSTOMER-A
 ip address 192.168.1.1/24
!
interface eth2
 description "Customer B"
 vrf CUSTOMER-B
 ip address 192.168.2.1/24
!

# Loopback
interface lo0
 ip address 1.1.1.1/32
!

# 主BGP配置
router bgp 65001
 bgp router-id 1.1.1.1
 bgp log-neighbor-changes
 
 # iBGP邻居 (路由反射器)
 neighbor 10.10.10.10 remote-as 65001
 neighbor 10.10.10.10 description "Route Reflector"
 neighbor 10.10.10.10 update-source lo0
 
 # IPv4地址族
 address-family ipv4 unicast
  neighbor 10.10.10.10 activate
  neighbor 10.10.10.10 next-hop-self
 exit-address-family
 
 # VPNv4地址族
 address-family ipv4 vpn
  neighbor 10.10.10.10 activate
  neighbor 10.10.10.10 send-community extended
 exit-address-family
 
 # L2VPN EVPN地址族
 address-family l2vpn evpn
  neighbor 10.10.10.10 activate
  neighbor 10.10.10.10 send-community extended
  advertise-all-vni
 exit-address-family
!

# 客户A的BGP配置
router bgp 65001 vrf CUSTOMER-A
 bgp router-id 1.1.1.1
 
 # 客户CE连接
 neighbor 192.168.1.2 remote-as 65101
 neighbor 192.168.1.2 description "Customer A CE"
 
 address-family ipv4 unicast
  neighbor 192.168.1.2 activate
  neighbor 192.168.1.2 soft-reconfiguration inbound
  
  # 路由目标
  rd 65001:1000
  rt import 65001:1000
  rt export 65001:1000
  
  # 重分发
  redistribute connected
 exit-address-family
!

# 客户B的BGP配置
router bgp 65001 vrf CUSTOMER-B
 bgp router-id 1.1.1.1
 
 # 客户CE连接
 neighbor 192.168.2.2 remote-as 65102
 neighbor 192.168.2.2 description "Customer B CE"
 
 address-family ipv4 unicast
  neighbor 192.168.2.2 activate
  neighbor 192.168.2.2 soft-reconfiguration inbound
  
  # 路由目标
  rd 65001:2000
  rt import 65001:2000
  rt export 65001:2000
  
  # 重分发
  redistribute connected
 exit-address-family
!
```

### 3.5 BGP 联邦配置

```frr
# BGP联邦配置
hostname Confederation-Router

interface lo0
 ip address 1.1.1.1/32
!

router bgp 65001
 bgp router-id 1.1.1.1
 bgp log-neighbor-changes
 
 # 联邦配置
 bgp confederation identifier 65000
 bgp confederation peers 65002 65003
 
 # 联邦内部邻居
 neighbor 2.2.2.2 remote-as 65001
 neighbor 2.2.2.2 description "iBGP within sub-AS"
 neighbor 2.2.2.2 update-source lo0
 neighbor 2.2.2.2 next-hop-self
 
 # 联邦间邻居
 neighbor 10.1.1.2 remote-as 65002
 neighbor 10.1.1.2 description "Confederation peer AS65002"
 
 # 外部邻居
 neighbor 10.2.1.2 remote-as 65100
 neighbor 10.2.1.2 description "External AS65100"
 
 address-family ipv4 unicast
  # 激活邻居
  neighbor 2.2.2.2 activate
  neighbor 10.1.1.2 activate
  neighbor 10.2.1.2 activate
  
  # 网络通告
  network 1.1.1.1/32
  network 192.168.1.0/24
  
  # 路由策略
  neighbor 10.2.1.2 route-map EXTERNAL-OUT out
 exit-address-family
!

# 外部路由策略
route-map EXTERNAL-OUT permit 10
 match ip address prefix-list INTERNAL-PREFIXES
 set as-path prepend 65000
!

ip prefix-list INTERNAL-PREFIXES seq 10 permit 192.168.0.0/16 le 24
!
```

### 3.6 完整生产环境配置

```frr
# 完整生产环境BGP配置
hostname Core-BGP-01

# 接口配置
interface lo0
 description "BGP Router ID"
 ip address 10.0.0.1/32
 ipv6 address 2001:db8:core::1/128
!

interface eth0
 description "eBGP to Upstream ISP"
 ip address 203.0.113.2/30
 ipv6 address 2001:db8:upstream::2/64
!

interface eth1
 description "iBGP to Core-02"
 ip address 10.1.1.1/30
!

interface eth2
 description "Customer Peering"
 ip address 10.2.1.1/30
!

# BGP主配置
router bgp 65001
 # 基本配置
 bgp router-id 10.0.0.1
 bgp log-neighbor-changes
 bgp deterministic-med
 bgp bestpath as-path multipath-relax
 bgp bestpath compare-routerid
 bgp bestpath med confed missing-as-worst
 
 # 优雅重启
 bgp graceful-restart
 bgp graceful-restart preserve-fw-state
 
 # 邻居组配置
 # iBGP邻居组
 neighbor IBGP-PEERS peer-group
 neighbor IBGP-PEERS remote-as 65001
 neighbor IBGP-PEERS update-source lo0
 neighbor IBGP-PEERS next-hop-self
 neighbor IBGP-PEERS send-community
 neighbor IBGP-PEERS send-community extended
 neighbor IBGP-PEERS timers 30 90
 
 # eBGP上游邻居组
 neighbor UPSTREAM-PEERS peer-group
 neighbor UPSTREAM-PEERS send-community
 neighbor UPSTREAM-PEERS soft-reconfiguration inbound
 neighbor UPSTREAM-PEERS timers 30 90
 
 # 客户邻居组
 neighbor CUSTOMER-PEERS peer-group
 neighbor CUSTOMER-PEERS send-community
 neighbor CUSTOMER-PEERS soft-reconfiguration inbound
 neighbor CUSTOMER-PEERS timers 60 180
 
 # 具体邻居配置
 # 上游ISP
 neighbor 203.0.113.1 peer-group UPSTREAM-PEERS
 neighbor 203.0.113.1 remote-as 65000
 neighbor 203.0.113.1 description "Upstream ISP"
 neighbor 203.0.113.1 password UpstreamSecret2024
 neighbor 203.0.113.1 bfd
 
 # iBGP邻居
 neighbor 10.0.0.2 peer-group IBGP-PEERS
 neighbor 10.0.0.2 description "Core-BGP-02"
 neighbor 10.0.0.3 peer-group IBGP-PEERS
 neighbor 10.0.0.3 description "Edge-BGP-01"
 
 # 客户邻居
 neighbor 10.2.1.2 peer-group CUSTOMER-PEERS
 neighbor 10.2.1.2 remote-as 65100
 neighbor 10.2.1.2 description "Customer-A"
 neighbor 10.2.1.2 password CustomerASecret
 
 # IPv4地址族
 address-family ipv4 unicast
  # 网络通告
  network 10.0.0.0/8
  network 192.168.0.0/16
  
  # 上游邻居
  neighbor 203.0.113.1 activate
  neighbor 203.0.113.1 prefix-list UPSTREAM-IN in
  neighbor 203.0.113.1 prefix-list OUR-PREFIXES out
  neighbor 203.0.113.1 route-map UPSTREAM-IN in
  neighbor 203.0.113.1 route-map UPSTREAM-OUT out
  
  # iBGP邻居
  neighbor IBGP-PEERS activate
  neighbor IBGP-PEERS route-reflector-client
  
  # 客户邻居
  neighbor 10.2.1.2 activate
  neighbor 10.2.1.2 prefix-list CUSTOMER-IN in
  neighbor 10.2.1.2 prefix-list CUSTOMER-OUT out
  neighbor 10.2.1.2 route-map CUSTOMER-IN in
  
  # 负载均衡
  maximum-paths 4
  maximum-paths ibgp 4
  
  # 聚合路由
  aggregate-address 192.168.0.0/16 summary-only
 exit-address-family
 
 # IPv6地址族
 address-family ipv6 unicast
  # IPv6邻居
  neighbor 2001:db8:upstream::1 remote-as 65000
  neighbor 2001:db8:upstream::1 activate
  neighbor 2001:db8:upstream::1 soft-reconfiguration inbound
  
  # 网络通告
  network 2001:db8::/32
  
  # 负载均衡
  maximum-paths 4
 exit-address-family
!

# 路由策略配置
# 上游入方向
route-map UPSTREAM-IN permit 10
 description "Accept default route from upstream"
 match ip address prefix-list DEFAULT-ONLY
 set local-preference 100
!

route-map UPSTREAM-IN permit 20
 description "Accept customer routes via upstream"
 match ip address prefix-list CUSTOMER-ROUTES
 set local-preference 80
!

route-map UPSTREAM-IN deny 30
!

# 上游出方向
route-map UPSTREAM-OUT permit 10
 description "Advertise our prefixes to upstream"
 match ip address prefix-list OUR-PREFIXES
 set as-path prepend 65001
!

route-map UPSTREAM-OUT deny 20
!

# 客户入方向
route-map CUSTOMER-IN permit 10
 description "Accept customer prefixes"
 match ip address prefix-list CUSTOMER-PREFIXES
 set local-preference 200
 set community 65001:100
!

route-map CUSTOMER-IN deny 20
!

# 前缀列表
ip prefix-list DEFAULT-ONLY seq 10 permit 0.0.0.0/0

ip prefix-list OUR-PREFIXES seq 10 permit 10.0.0.0/8
ip prefix-list OUR-PREFIXES seq 20 permit 192.168.0.0/16

ip prefix-list CUSTOMER-PREFIXES seq 10 permit 172.16.0.0/12 le 24

ip prefix-list UPSTREAM-IN seq 10 permit 0.0.0.0/0
ip prefix-list UPSTREAM-IN seq 20 permit 0.0.0.0/0 le 24

ip prefix-list CUSTOMER-IN seq 10 permit 172.16.0.0/12 le 24
ip prefix-list CUSTOMER-IN seq 20 deny 0.0.0.0/0 le 32

ip prefix-list CUSTOMER-OUT seq 10 permit 0.0.0.0/0
ip prefix-list CUSTOMER-OUT seq 20 permit 10.0.0.0/8 le 24
!

# AS路径列表
bgp as-path access-list UPSTREAM-AS permit ^65000
bgp as-path access-list CUSTOMER-AS permit ^65100

# 团体列表
bgp community-list standard CUSTOMER-ROUTES permit 65001:100
bgp community-list standard NO-EXPORT permit no-export
!

# BFD配置
bfd
 peer 203.0.113.1
  detect-multiplier 3
  receive-interval 300
  transmit-interval 300
 !
!
```

## 4. 配置验证命令

### 4.1 基本状态检查
```bash
# 查看BGP进程状态
vtysh -c "show bgp summary"

# 查看邻居状态
vtysh -c "show bgp neighbors"

# 查看路由表
vtysh -c "show bgp ipv4 unicast"
vtysh -c "show bgp ipv6 unicast"

# 查看特定前缀
vtysh -c "show bgp ipv4 unicast 192.168.1.0/24"
```

### 4.2 详细诊断命令
```bash
# 查看邻居详细信息
vtysh -c "show bgp neighbors 10.1.1.2 advertised-routes"
vtysh -c "show bgp neighbors 10.1.1.2 received-routes"

# 查看路由属性
vtysh -c "show bgp ipv4 unicast 192.168.1.0/24 bestpath"

# 查看统计信息
vtysh -c "show bgp statistics"

# 查看内存使用
vtysh -c "show bgp memory"
```

### 4.3 故障排除命令
```bash
# 软重置邻居
vtysh -c "clear bgp ipv4 unicast 10.1.1.2 soft in"

# 硬重置邻居
vtysh -c "clear bgp ipv4 unicast 10.1.1.2"

# 查看调试信息
vtysh -c "debug bgp neighbor-events"
vtysh -c "debug bgp updates"
```

## 5. 常见配置模板

### 5.1 最小 eBGP 配置模板
```frr
router bgp 65001
 bgp router-id 1.1.1.1
 neighbor 10.1.1.2 remote-as 65002
 address-family ipv4 unicast
  neighbor 10.1.1.2 activate
  network 192.168.1.0/24
 exit-address-family
!
```

### 5.2 标准企业 iBGP 配置模板
```frr
router bgp 65001
 bgp router-id 1.1.1.1
 bgp log-neighbor-changes
 neighbor 2.2.2.2 remote-as 65001
 neighbor 2.2.2.2 update-source lo0
 neighbor 2.2.2.2 next-hop-self
 address-family ipv4 unicast
  neighbor 2.2.2.2 activate
  neighbor 2.2.2.2 soft-reconfiguration inbound
  maximum-paths ibgp 4
 exit-address-family
!
```

### 5.3 ISP 边界配置模板
```frr
router bgp 65001
 bgp router-id 1.1.1.1
 bgp log-neighbor-changes
 bgp bestpath as-path multipath-relax
 
 # 上游ISP
 neighbor 203.0.113.1 remote-as 65000
 neighbor 203.0.113.1 password secret
 
 address-family ipv4 unicast
  neighbor 203.0.113.1 activate
  neighbor 203.0.113.1 soft-reconfiguration inbound
  neighbor 203.0.113.1 prefix-list UPSTREAM-IN in
  neighbor 203.0.113.1 prefix-list OUR-PREFIXES out
  network 192.168.0.0/16
 exit-address-family
!

ip prefix-list UPSTREAM-IN seq 10 permit 0.0.0.0/0
ip prefix-list OUR-PREFIXES seq 10 permit 192.168.0.0/16
!
```

这个总结涵盖了 BGP 的所有核心配置项和实际应用场景，包括 eBGP、iBGP、路由反射器、MPLS VPN、联邦等各种部署模式，可以作为 BGP 配置的完整参考。