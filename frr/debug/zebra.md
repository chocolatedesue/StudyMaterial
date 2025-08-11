我会查看 docker/centos-8/docker-start 了解该环境的启动脚本是否加载了内核模块或做了其他操作，从而判断是否会导致内核事件风暴影响 zebra。

我会查看默认的 zebra 配置模板，判断是否默认启用了 FPM 或其他可能导致高 CPU 的功能。这样可以确认“无配置时”zebra 是否仍会做额外工作。

## 你的容器里 zebra 是怎么被拉起来的

- centos-8 的启动脚本会直接用 watchfrr 启动所有“被认为启用”的守护进程；它是通过 frrcommon.sh 的 daemon_list 来决定的：
````bash path=docker/centos-8/docker-start mode=EXCERPT
source /usr/lib/frr/frrcommon.sh
/usr/lib/frr/watchfrr $(daemon_list)
````
- 默认情况下只会启动 zebra（可能还有 staticd，取决于安装/编译）。你说“只有 zebra 运行”基本符合这个脚本行为。

## zebra 启动后的核心流程（精简）

- 初始化：打开 Netlink（Linux）监听内核事件、启动 ZAPI（给 bgpd/ospfd 等来连）、启动 VTY/CLI。
- 全量同步：从内核 dump 接口/地址/邻居/路由，建立内部视图。
- 持续循环：
  - 接内核事件（链路/地址/邻居/路由变更），更新 RIB/FIB。
  - 接协议守护进程的路由通告（你没起协议进程时这部分为空）。
  - 解析下一跳、编程内核 FIB、必要时回通告。

即使没有配置协议，zebra 也会持续消费内核的 Netlink 事件流。

## 仅启动 zebra 占用 CPU 高的常见原因

- 内核事件风暴或持续抖动
  - 容器/宿主上接口、邻居（ARP/ND）、路由频繁变更，会触发 zebra 不断处理事件。
  - 大量容器侧邻居探测/超时也能制造 NEIGH 事件洪水。

- Netlink 接收缓冲过小导致丢包→zebra 反复重同步
  - 出现 ENOBUFS/overrun 时，zebra 会触发整表重新 dump 以求一致；如果事件持续，形成“事件多→丢包→重同步→更忙”的循环。

- 路由/邻居规模偏大
  - 即便没有协议守护进程，容器环境的邻居/接口数量、转发表规模也可能不小，一次 dump/重算就很重。

- 外部导出/管道阻塞（如果启用了）
  - 开了 FPM（向外部导出 FIB）但对端慢或不可达，会拖累 dataplane 线程，导致 CPU 持续高。

## 快速定位清单（优先级从上到下）

在容器里运行 vtysh（可逐条执行）：
- 看 CPU 热点线程
  - show thread cpu
  - show thread cpu zebra
  - 重点看 netlink 读、dataplane、zapi 哪个线程热。
- 看内核/数据面队列是否堆积
  - show dataplane status
  - show route pending（不同版本命令略有差异，关注 pending/queued）
- 看接口/邻居是否在抖
  - show interface brief
  - show ipv6 neighbors / show ip neighbors（命令名依版本不同，可先 show ? 搜索）
- 打开短时间内核调试日志，确认是否频繁重同步或事件过多
  - configure terminal
  - log file /var/log/frr/zebra-debug.log
  - debug zebra kernel
  - 过一两分钟后 undebug zebra kernel，然后检查日志里是否有 ENOBUFS/overrun/resync 之类的字样。

系统/日志侧：
- journalctl -u frr 或 zebra 的专用日志，搜索 netlink、ENOBUFS、overrun、dump/resync 等关键字。

## 缓解与优化建议

- 减少抖动源
  - 排查是否有接口 flap、容器网络频繁变更、ARP/ND 风暴。
  - 若 IPv6 不用，可暂时在宿主/容器禁用 IPv6（会显著减少 ND 事件）。

- 增大 Netlink 缓冲，避免 ENOBUFS
  - 在 zebra 配置里（conf 模式）设置较大的 netlink 缓冲（命令名依版本不同，常见为 netlink-buffer-size 字节数），例如：
    - netlink-buffer-size 16777216
  - 系统层也可调大 net.core.rmem_max、net.core.rmem_default，并确保容器有相应权限。

- 控制规模与导出
  - 未使用 FPM 就不要启用；若启用，确保对端性能/带宽充足。
  - 避免无必要的全量 redistribute（虽然后者更多发生在协议守护进程场景）。

- 线程热点对症优化
  - 若 dataplane/FIB install 热：检查是否存在频繁路由安装/撤销；合并批处理窗口（版本相关）。
  - 若 netlink 读热：优先解决 ENOBUFS 与外部事件量问题。

## 你可以提供的信息（我可进一步定点建议）

- show thread cpu zebra 的输出前几行
- zebra-debug.log 中是否出现 ENOBUFS/overrun 或频繁 “dump/resync”
- 接口/邻居是否频繁变化（show interface brief、邻居表）
- 是否开启了 FPM 或其他导出

我也可以给你一套“复制即用”的 vtysh 命令脚本，用来短时间采样并输出诊断结果，便于快速判断 CPU 高的根因方向。
