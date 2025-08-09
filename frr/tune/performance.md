这是一份关于 FRRouting (FRR) 性能优化的实用指南，已翻译成中文。

## 快速背景检查

FRRouting (FRR) 的性能调优很大程度上取决于您的具体使用场景（例如，路由反射器还是边缘路由器，仅使用 IGP 还是 BGP，路由规模，收敛速度与 CPU/内存的优先级，硬件/操作系统）。以下是一些实用、低风险的优化措施。如果您能分享您的协议组合、路由数量和一些 “show …” 命令的输出，我可以更精确地为您定制这份列表。

---

## 高影响、低风险的快速优化

- 在生产环境中关闭所有调试日志。将日志级别保持在警告或错误。
- 避免在 BGP 邻居上使用 “soft-reconfiguration inbound”；依赖路由刷新（route-refresh）来节省内存和 CPU。
- 仅启用您实际需要的地址族（address families）和功能。
- 对于大型会话/路由规模，增加文件描述符限制和 systemd 限制（ulimit -n, TasksMax）。
- 在繁忙的设备上，将 zebra 和 bgpd（以及其他守护进程）分离到不同的 CPU 核心上（CPU 亲和性）。

---

## Linux 内核和网络 sysctls

调优以应对大型控制平面突发和 netlink 流量。以下是一些基准示例：

- **套接字和积压队列 (Sockets and backlog)**
  - `net.core.rmem_max` / `wmem_max`: 至少 16–64 MB（`rmem_default` / `wmem_default` 相应调整）
  - `net.core.netdev_max_backlog`: 250000（或根据网卡吞吐量预期调整）
  - `net.core.somaxconn`: 4096+
- **适用于大量 BGP 会话的 TCP**
  - `net.ipv4.tcp_max_syn_backlog`: 4096+
  - `net.ipv4.tcp_timestamps=1`, `tcp_sack=1`（大多数现代内核的默认值）
  - `net.ipv4.ip_local_port_range`: `1024 65000`（或根据您的策略调整）
- **邻居/ARP/ND 扩展**
  - `net.ipv4.neigh.default.gc_thresh1/2/3`: `4096/8192/16384`（在大型 L3 网络中可设置更高）
  - IPv6 等效项: `net.ipv6.neigh.default.gc_thresh1/2/3`
- **多路径 (如果使用 ECMP)**
  - `net.ipv4.fib_multipath_hash_policy=1`（在支持的情况下启用 L3+L4 哈希）
  - `net.ipv4.fib_multipath_use_neigh=1`（在某些场景下可以提高收敛速度）

注意：请逐步应用并进行监控；具体值取决于内存/流量。

---

## FRR zebra/数据平面考量

- **将 zebra 和 bgpd 放在不同的 CPU 上**，以减少资源争用；通过 `systemd CPUAffinity` 或 `taskset` 绑定守护进程。
- **确保 NIC/RSS 和 RPS/XPS 配置正确**，以分散中断请求（IRQs），避免 zebra 与单个繁忙的 CPU 竞争。
- **如果要安装非常大的路由突发**，增加内核套接字缓冲区（见上文）可以减少 netlink 丢包/重试。
- **如果您不需要某些内核功能**（例如，超过几个路径的多路径），保持 ECMP 宽度适中，以减少 FIB 频繁变更。

---

## BGP 特定调优

- **内存/处理**
  - 避免 “soft-reconfiguration inbound”，除非必要；它会在内存中存储 Adj-RIB-In。
  - **简化策略**：优先使用特定且已编译（有序、最小化）的 **prefix-lists** / **route-maps**。
  - 如果您不使用某些社区或属性，限制其处理。
- **抖动控制和稳定性**
  - 在路由反射器（RRs）上，使用小的非零值 **MRAI/advertisement-interval** 来平滑突发更新，以防出现更新风暴。
  - 谨慎使用路由震荡抑制（route dampening）（通常不需要，且会增加 CPU 负载）。
  - 对于启动风暴，考虑使用短暂的 `bgp update-delay`，以便 IGP/下一跳跟踪（NH tracking）先稳定下来。
- **计时器**
  - 保持邻居计时器在合理范围（例如，`15/45` 用于 KA/HOLD），除非您需要亚秒级的故障切换。
  - 在 eBGP 边缘使用 `fast-external-fallover`，以便在链路故障时快速断开会话。
- **功能**
  - 仅在需要时使用 `add-path`、`wide/extended messages` 和 `large communities`——每个功能都可能增加 CPU/内存开销。
  - 避免为每个对等体使用不必要的地址族和 AFI/SAFI。

---

## IGP (OSPF/ISIS) 调优以平衡收敛速度与 CPU

- **当处理许多抖动时，限制 SPF/LSA**：
  - **OSPF**: 使用 `timers throttle spf` 和 `timers throttle lsa` 在不稳定期间进行退避。
  - **ISIS**: 类似地设置 `spf-intervals`。
- **减少 LSA/LSP 抖动**：通过自动化或遥测驱动的策略，尽量减少频繁的开销/度量值变更。

---

## 日志和持久性

- **日志**
  - **日志级别**：生产环境中设置为 `warnings` 或 `errors`；发送到 syslog/journal（避免同步的控制台日志）。
  - **不要启用任何按协议的调试日志**。
- **配置写入**
  - 避免通过自动化频繁执行 `write memory`；批量进行配置更改，以减少磁盘 I/O 和配置解析器的 CPU 消耗。

---

## 进程、内存分配器和 systemd 提示

- 在密集部署中，为 `bgpd`/`zebra` 的 unit overrides 增加 **NOFILE ulimit**（例如，`262144`）。
- 对于 `glibc`，考虑设置 `MALLOC_ARENA_MAX=4`，以减少长时间运行的守护进程中的碎片。
- 在 NUMA 系统上，将相关的守护进程保持在同一 NUMA 节点上，避免跨节点争用。
- 保持操作系统更新；较新的内核通常会改善 netlink 的可扩展性和 FIB 性能。

---

## 策略和配置规范

- 保持 **prefix-lists** 和 **route-maps** 紧凑且有序，将最精确的匹配项放在前面。
- 避免使用大型链式 **route-maps**，一个精心设计的映射就足够了。
- 优先使用简单的 **communities** 或 **communities-regex** 匹配；大规模使用复杂的正则表达式会占用大量 CPU。
- 删除未使用的邻居、地址族和重分发（redistribute）声明。

---

## 衡量指标（以指导调优）

偶尔运行以下命令来识别热点：
- `show thread cpu`
- `show memory [daemon]`
- `show route summary`
- `show bgp summary`
- `show bgp neighbors [x] advertised-routes` / `received-routes`（用于查看规模）
- `show zebra clients summary`
- **系统层面**：`pidstat/top/htop` 查看 CPU 分布；`ss -tan` 计算 TCP 状态；`dmesg` 查找 netlink 警告。

如果您看到：
- **bgpd 的 CPU 很高**：检查策略复杂性、对等体数量、更新抖动；减少功能或添加 CPU 绑定。
- **zebra 的 CPU 很高**：FIB 编程突发；增加套接字缓冲区，减少 ECMP 宽度，放慢更改速度（策略抖动）。
- **内存压力**：移除 `soft-reconfig inbound`，减少属性，精简策略，设置 `MALLOC_ARENA_MAX`。

---

## 可选的高级项目（有选择地使用）

- 对于处理超过 1M 路由的路由反射器：考虑适度的 MRAI，简化策略，确保足够的内存；将 bgpd 绑定到专用核心。
- 仅在诊断出内存分配器热点后，才考虑使用 **jemalloc/tcmalloc**；在生产环境中使用前请仔细测试。
- **ECMP 宽度**：在构建时或通过配置限制其宽度，以减少 FIB 抖动。

---

## 想要定制化的建议吗？

请分享以下信息：
- 正在使用的协议（BGP/OSPF/ISIS）、路由反射器或边缘角色、大致的路由数量和邻居数量
- 内核版本和硬件（CPU 核心、RAM、NUMA）
- 几张快照：`show thread cpu`、`show route summary`、`show bgp summary`
- 您的优先级是**最快收敛**还是**最低 CPU/内存占用**

我将根据这些信息为您制定一个具体、最小化的变更计划。