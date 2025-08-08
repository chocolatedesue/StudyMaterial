我先快速查一下仓库文档/代码里关于 zebra 是否会创建网卡、哪些场景（如 EVPN/VXLAN、VRF）会由 zebra 自动创建接口的说明，以确保回答准确。

## 结论先说
- 一般情况下，zebra不会“随意创建”Linux网卡，它负责把你在配置里写的接口/IP等意图同步到内核。
- 你可以在 zebra.conf/frr.conf 里“声明接口并配置 IP”，zebra 会把地址下发到内核。即便接口当下不存在，接口稍后出现时也会自动应用。
- 只有少数场景（如 EVPN/VXLAN、部分 L2/L3 设备）zebra 会根据控制面配置自动创建相关虚拟网卡；普通以太、dummy/veth/tap 等需你在系统层面预先创建。

下面给出可操作方法与注意点。

---

## 方式一：预先创建网卡，zebra 负责分配 IP（最通用）
步骤：
1) 在 Linux 侧创建/准备好网卡（例如 dummy0、vlan、veth、物理口等）
   - 例：ip link add dummy0 type dummy；ip link set dummy0 up
2) 在 zebra.conf 里配置接口与地址
3) 重载/重启 FRR，zebra 会把地址写入内核；如果接口稍后才出现，zebra 会延后应用

示例（zebra.conf 片段，接口已在系统存在）：
````text path=examples/zebra.conf mode=EXCERPT
log file /var/log/frr/zebra.log debugging
interface dummy0
 ip address 192.0.2.1/24
 ipv6 address 2001:db8::1/64
````

要点：
- 你可以先在 FRR 配好 interface dummy0/ip address；即使 dummy0 暂时不存在，等它由系统创建、内核上报后，zebra 会自动把地址下发。
- 查看效果：vtysh -c "show interface dummy0"、"show ip/ipv6 interface"、"show ip/ipv6 route connected"

---

## 方式二：带 VRF 的自动应用（接口出现即入 VRF 并分配 IP）
前提：Linux 中已创建 VRF 设备（VRF_Lite）或使用 netns。FRR 不负责创建 VRF netdev，本机需要：
- ip link add vrf-blue type vrf table 1001
- ip link set vrf-blue up
-（可选）把某物理/虚拟口加入 VRF：ip link set eth1 master vrf-blue

在 FRR 侧（zebra.conf）：
````text path=examples/zebra-vrf.conf mode=EXCERPT
vrf blue
interface eth1 vrf blue
 ip address 10.10.1.1/24
````

要点：
- 这里的 interface eth1 vrf blue 也可以由 FRR 来“绑定”接口到 VRF（通过 netlink），但 VRF 设备本身需事先存在。
- 路由查看：vtysh -c "show ip route vrf blue"、"show interface brief vrf blue"

---

## 方式三：EVPN/VXLAN 等场景由 zebra 自动创建相关网卡（特定场景）
- 当你在 BGP EVPN 中配置 VNI、桥域、访问/网络侧接口时，bgpd+zebra 会通过 netlink 自动创建并维护 vxlan、bridge、vlan SVI 等设备，并为 SVI/loopback 配置地址（按你的配置）。
- 这是“受控”的自动创建，仅限相关类型（VXLAN/bridge/VLAN/GRE 等）；普通以太、dummy、veth 并不会被自动创建。
- 这类配置较多、依赖版本特性，建议在你现有拓扑/需求上再具体给出模板。

---

## 验证与排障
- 查看接口/地址：
  - vtysh -c "show interface brief"
  - vtysh -c "show interface IFNAME"
  - vtysh -c "show ip interface" / "show ipv6 interface"
- 查看连接路由（connected 是否已入内核）：
  - vtysh -c "show ip route summary" / "show ipv6 route summary"
- 观察“自动应用”的过程（读入配置、与内核交互）：
  - 在 zebra.conf 中添加日志：
    - log file /var/log/frr/zebra.log debugging
    - log commands
  - 开启关键调试（临时）：
    - vtysh -d zebra -c "conf t" -c "debug zebra kernel" -c "debug zebra kernel msgdump recv"
  - tail -f /var/log/frr/zebra.log

---

## 常见问题
- 为什么“接口不存在但我在 zebra.conf 里写了地址”也能生效？
  - FRR 会保存这份“意图配置”；当内核上报接口出现（RTM_NEWLINK）时，zebra 自动把地址等属性应用过去。
- 能不能用 FRR 创建普通网卡（dummy/veth/tap/物理口）？
  - 不能；请用 ip link/网络管理器等在系统层创建。FRR 只管理其属性（IP/mtu/VRF 绑定等）并做路由/邻居/内核编程。
- VRF 设备谁创建？
  - 通常由系统（ip link add vrf ...）或容器/netns 方案创建；FRR 识别并管理之。接口加入 VRF 可由 FRR 或系统完成，但 VRF netdev 要先有。

---

如果你告诉我期望创建的接口类型（普通以太/Loopback/dummy/VLAN/VXLAN/VRF）和目标 IP/VRF，我可以给出一份适配你环境的最小配置片段；EVPN/VXLAN 场景也可以给出可直接落地的示例。
