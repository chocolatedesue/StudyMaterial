## 目标
只优化“启动-建邻”这一个阶段，降低瞬时 CPU 抖动；稳态运行阶段保持较快的收敛。推荐“分两阶段配置”的思路：启动阶段启用更强的节流/批处理/延迟；拓扑稳定后再切换到日常的较快参数。

---

## 总体方案（两阶段配置）
- 阶段A（启动/建邻降负配置）
  - 目的：抑制 SPF/洪泛/内核编程风暴，平滑 CPU 峰值
  - 手段：OSPFv3/IS‑IS 的 SPF 自适应节流、更大的 LSA/LSP 时间间隔；zebra 侧加大批处理窗口、降低单轮处理包数；内核 Netlink 批量发送
- 阶段B（稳态/快速收敛配置）
  - 目的：在邻接和 LSDB 稳定后还原较快的定时器和策略，提高后续收敛速度

切换方式
- 使用 frr-reload 增量加载稳态配置；或 vtysh 执行少量 CLI 变更
- 触发策略：
  - 定时（例如启动后 T=120–300s）；
  - 或“邻接稳定检测”后再切换（更稳妥）

---

## 阶段A：启动/建邻“降负”参数建议

### zebra（所有协议共用，强烈推荐）
- zebra work-queue 100–200
  - 增大 RIB 工作队列 hold，批处理/节流路由更新
- zebra zapi-packets 300–600
  - 单轮 ZAPI 包处理量下调，增加让出频率，平滑 CPU
- zebra kernel netlink batch-tx-buf 262144 196608（或 524288 458752）
  - 增大内核写入批处理缓冲/阈值，减少 syscall 次数
- 启动参数（Linux）：zebra --nl-bufsize 262144（接收缓冲更大）

说明：这些只影响峰值形态、不会变更协议行为，适合整个生命周期保持，或仅在启动阶段使用更“保守”的取值。

### OSPFv3（ospf6d）
- timers throttle spf 200 1000 10000
  - 自适应节流：初始/短期/上限，强力抑制事件风暴期间的重复 SPF
- timers lsa min-arrival 1000
  - 同一 LSA 到达抖动抑制
- write-multiplier 15–20
  - 写线程单轮工作量；适度下调更平滑
- 接口 hello/dead/retransmit/transmit-delay：一般维持默认（10/40/5/1），避免延后建邻；如邻接面非常多，可临时将 hello 调到 15、dead 60（权衡收敛速度）

可选（对 CPU 间接帮助）：
- graceful-restart enable + interface hello-delay 10–20
  - 避免重启瞬时的 hello 互相干扰，优先完成 GR 通告

### IS‑IS（isisd）
- spf-delay-ietf init 200 short 500 long 5000 holddown 10000 time-to-learn 1000
  - IETF SPF backoff 算法，比固定最小间隔更智能地抑制风暴
  - 若不启用 backoff：spf-interval level-1 3 / level-2 3
- lsp-gen-interval level-1 5 / level-2 5
  - 限制频繁重组 LSP 的速率
- csnp-interval level-1 20 / level-2 20，psnp-interval level-1 10 / level-2 10
  - 降低数据库同步 PDU 的频率
- set-overload-bit on-startup 120–300
  - 启动时设置 overload bit，避免未稳定前转发中转流量（不给 CPU背压）；到时自动清除

可选（分批建邻）
- 在启动配置里，先将边缘/大量口设置为 passive（OSPFv3: ipv6 ospf6 passive；IS‑IS: isis passive），只放开骨干/关键口；LSDB 稳定后再取消 passive，分批建邻可显著平滑峰值

---

## 阶段B：稳态/快速收敛参数建议
- OSPFv3
  - timers throttle spf 50 200 2000
  - timers lsa min-arrival 200–300
  - write-multiplier 恢复 20–30
- IS‑IS
  - spf-delay-ietf 参数整体下调（例如 init 50 short 200 long 2000 holddown 3000 learn 500），或 spf-interval 1–2
  - lsp-gen-interval 恢复默认（通常 2s）
  - csnp/psnp-interval 恢复默认（更快同步）
  - overload-bit 无需变更，on-startup 自行到时清除
- zebra
  - 可保持大 netlink 批处理（对稳态副作用小）
  - work-queue 可从 100–200 降到 10–50；zapi-packets 1000

---

## 切换实现方式

### 方案1：定时 reload（简单可靠）
1) 准备两份配置：
   - /etc/frr/frr-startup.conf（含上述“阶段A”更保守参数，可能还包含部分接口 passive）
   - /etc/frr/frr-steady.conf（“阶段B”较快参数，并移除 passive）
2) 以启动配置启动 FRR
3) T+180s（或你评估所需时间）后，执行增量 reload 到稳态配置

命令示例
- 使用 frr-reload.py（Python 脚本）：按你的要求用 uv run 调用
  - uv run /usr/lib/frr/frr-reload.py --reload -f /etc/frr/frr-steady.conf
- 或者使用 vtysh 执行必要的几条命令（对比两份配置后仅应用差异）

systemd 自动化（示例思路）
- 在 frr.service 增加一个 ExecStartPost 脚本，sleep 指定秒数后执行上述 uv run reload
- 更稳妥：写一个健康检查脚本，轮询“邻接数是否达到预期、LSDB 不再增长”后再触发 reload

### 方案2：基于“邻接稳定”的条件 reload（更稳妥）
- 周期性检查：
  - show isis neighbor json / show ipv6 ospf6 neighbor json（vtysh）
  - show isis database summary / show ipv6 ospf6 database summary（增长停止）
- 满足门限后执行 uv run frr-reload.py 切换到稳态配置

备注
- frr-reload.py 会尽量“无扰动增量应用”，更适合做阶段切换
- 仅当差异较小时，也可直接 vtysh -c 执行几条命令

---

## 可选加固（按需选）
- 分批 bring-up 接口：在启动配置里仅开放核心接口，其余接口保持 passive；分批 reload 放开
- 启动时暂缓 redistribute（OSPFv3/IS‑IS），待 LSDB 稳定后再开启，减少初期路由注入压力
- 临时关闭 LFA/TI‑LFA 计算，稳态再开启（IS‑IS：fast-reroute ...）

---

## 验证与回退
- 观察指标
  - CPU 峰值、抖动幅度（启动 5–10 分钟）
  - 邻接收敛时延、LSDB 大小增长曲线
  - zebra show dplane、内核 netlink 发送批量日志
- 若 CPU 仍有尖峰
  - 进一步增大 OSPFv3/IS‑IS 的 backoff/interval
  - zebra work-queue 再上调（到 200），zapi-packets 再下调（到 300）
  - 分批建邻力度加大（更多口 passive，第二次/第三次再放开）

---

## 我可以帮你“落地两份配置”
- 告诉我：
  - 典型邻接数量/LSDB 规模（大概量级）
  - 期望“启动后进入稳态”的时间窗（例如 2–5 分钟）
  - 是否需要分批建邻（按接口/VRF 列出优先级）
- 我会给出：
  - frr-startup.conf 与 frr-steady.conf 的最小差异集
  - 一个基于 uv run 的 reload 脚本（定时或基于邻接稳定检测）
  - 验证指令清单（show/日志点）与回退步骤

如需，我也可以先给出一个“通用模板”的两份配置草案，你再按接口/VRF 名称替换后直接试运行。
