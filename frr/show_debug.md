## 目标
梳理在 FRR 中用于“查看当前系统运行状态”的常用 show 命令，按守护进程分组：zebra、bgpd、ospf6d、isisd。命令既可在 vtysh 统一入口直接敲，也可用 vtysh -d <daemon> -c "cmd" 直达对应进程。

---

## Zebra（内核/接口/路由表）
- 接口与地址
  - show interface brief
  - show interface IFNAME
  - show ip interface
  - show ipv6 interface
  - show interface vrf all 或 show interface brief vrf NAME
- 路由/RIB/内核同步
  - show ip route
  - show ip route summary
  - show ipv6 route
  - show ipv6 route summary
  - 按 VRF：show ip route vrf NAME、show ipv6 route vrf NAME
  - 按协议过滤（示例）：show ip route protocol static
- VRF 与平台
  - show vrf
  - show vrf detail
- 日志/调试状态
  - show logging
  - show debugging zebra

小贴士：zebra 是“总控 + 内核编程”，快速判断“内核里到底有什么”以 show ip/ipv6 route 和 ip/ipv6 interface 为主。

---

## BGP（bgpd）
- 总体健康
  - show bgp summary
  - IPv4/IPv6 单播分家：show bgp ipv4 unicast summary、show bgp ipv6 unicast summary
  - VRF：show bgp vrf NAME summary
- 邻居与会话
  - show bgp neighbor
  - show bgp neighbor A.B.C.D
  - show bgp neighbor A.B.C.D advertised-routes
  - show bgp neighbor A.B.C.D received-routes
- BGP 路由表/前缀
  - IPv4：show bgp ipv4 unicast
  - IPv6：show bgp ipv6 unicast
  - 按前缀：show bgp ipv4 unicast PREFIX、show bgp ipv6 unicast PREFIX
  - 全表统计：show bgp table
- 策略与社区（常用）
  - show route-map
  - show ip prefix-list / show ipv6 prefix-list
  - show community-list

---

## OSPFv3（ospf6d）
- 总体与邻居
  - show ipv6 ospf6
  - show ipv6 ospf6 neighbor
  - show ipv6 ospf6 neighbor detail
- 接口与区域
  - show ipv6 ospf6 interface
  - show ipv6 ospf6 interface IFNAME
  - show ipv6 ospf6 area
- 链路状态数据库（LSDB）
  - show ipv6 ospf6 database
  - 精确类型（示例）：show ipv6 ospf6 database router、network、inter-prefix、as-external、intra-prefix 等
  - 加 detail 查看细节
- 路由
  - show ipv6 ospf6 route

---

## IS-IS（isisd）
- 总体/实例
  - show isis summary
  - 多实例时：show isis instance
- 邻居与接口
  - show isis neighbor
  - show isis neighbor detail
  - show isis interface
- 拓扑与数据库
  - show isis database
  - show isis database detail
  - show isis topology
- 路由
  - show isis route

---

## 跨守护进程的通用状态
- 版本/进程
  - show version
- 运行配置（可比对“意图 vs 实际”）
  - show running-config
  - 单进程：show running-config zebra / bgpd / ospf6d / isisd
- 资源与线程（排障用）
  - show memory
  - show thread cpu

---

## 常见查看路径（建议顺序）
- 全局与接口
  - show interface brief
  - show vrf
- 核心路由表（是否已下到内核）
  - show ip route summary
  - show ipv6 route summary
- 按协议深入
  - BGP：show bgp summary → show bgp neighbor → show bgp ipv4/ipv6 unicast
  - OSPFv3：show ipv6 ospf6 neighbor → show ipv6 ospf6 database → show ipv6 ospf6 route
  - IS-IS：show isis summary → show isis neighbor → show isis database → show isis route
- 如遇不一致，回看意图配置和日志
  - show running-config [daemon]
  - show logging、show debugging [daemon]

---

## VRF 场景要点
- 接口/路由普查
  - show interface brief vrf all
  - show ip route vrf NAME、show ipv6 route vrf NAME
- BGP VRF
  - show bgp vrf NAME summary
  - show bgp vrf NAME ipv4/ipv6 unicast

---

如果你告诉我当前启用了哪些守护进程、是否使用 VRF，以及你想确认的侧重点（邻居、路由收敛、内核表、策略匹配等），我可以给出一组更精确的一键命令组合和解读要点。
