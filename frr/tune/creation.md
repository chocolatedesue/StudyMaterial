我会在代码和文档里检索 OSPFv3 与 ISIS 的调优命令、默认值和范围（如 SPF 节流、LSA/LSP 生成与到达、Hello/Dead、CSNP/PSNP、BFD、GR/overload bit 等），以便给出权威列表并突出“建拓扑降负”优先项。

## 背景
针对“拓扑初建时的计算开销”，OSPFv3(ospf6d) 与 IS-IS(isisd) 都提供了节流/批处理/抑制风暴的调优项。下面按“重要性与场景”给出可调参数、默认/范围与建议值，并标注代码/文档出处，便于你核对。

---

## OSPFv3（ospf6d）调优重点

### 1) SPF 自适应节流（强烈推荐）
- 命令（进程级）
  - timers throttle spf <delay-ms> <init-hold-ms> <max-hold-ms>（0–600000）
- 作用
  - 批量化并自适应回退，平滑频繁事件引发的 SPF 计算
- 参考设置（初建降负）
  - 200 400 10000 或 200 1000 10000（更稳）
- 依据
````text path=doc/user/ospf6d.rst mode=EXCERPT
.. clicmd:: timers throttle spf (0-600000) (0-600000) (0-600000)
...
router ospf6
 timers throttle spf 200 400 10000
````
<augment_code_snippet path="ospf6d/ospf6_spf.c" mode="EXCERPT">
```c
/* holdtime 自适应直到 max_holdtime */
if (ht < ospf6->spf_max_holdtime)
    ospf6->spf_hold_multiplier++;
```
</augment_code_snippet>

### 2) LSA 最小到达间隔（建议）
- 命令（进程级）
  - timers lsa min-arrival <0–600000ms>
- 作用
  - 抑制同一 LSA 频繁到达导致的计算/洪泛抖动
- 参考设置（初建/收敛期）
  - 500–1000ms
- 依据
````c path=ospf6d/ospf6_top.c mode=EXCERPT
"timers lsa min-arrival (0-600000)"
...
if (ospf6->lsa_minarrival != OSPF_MIN_LS_ARRIVAL)
    vty_out(vty, " timers lsa min-arrival %d\n", ospf6->lsa_minarrival);
````

### 3) 写入批处理让出（写线程工作量）
- 命令（进程级）
  - write-multiplier (1–100), 默认 20
- 作用
  - 控制每次写线程处理的接口个数，偏向“多让出，少峰值”
- 建议
  - 维持默认 20；CPU 峰值明显时可短暂降为 10–15 换更平滑但略慢
- 依据
````text path=doc/user/ospf6d.rst mode=EXCERPT
.. clicmd:: write-multiplier (1-100)
... default value ... 20
````

### 4) Hello/Dead/重传/发送延时（接口级）
- 命令
  - ipv6 ospf6 hello-interval 1–65535（默认 10）
  - ipv6 ospf6 dead-interval 1–65535（默认 40）
  - ipv6 ospf6 retransmit-interval 1–65535（默认 5）
  - ipv6 ospf6 transmit-delay 1–3600（默认 1）
- 建议
  - 大多数场景保留默认；邻居规模极大且 CPU 紧张时，可适度增大 hello（权衡收敛）
- 依据（文档中含默认值说明）
````text path=doc/user/ospf6d.rst mode=EXCERPT
ipv6 ospf6 hello-interval ... Default 10
ipv6 ospf6 dead-interval ... Default 40
ipv6 ospf6 retransmit-interval ... Default 5
ipv6 ospf6 transmit-delay ... Default 1
````

### 5) GR hello-delay（可选）
- 命令（接口级）
  - ipv6 ospf6 graceful-restart hello-delay <sec>（默认 10）
- 作用
  - 重启回收阶段延后 hello，优先完成 Grace-LSA 通告；非直接“降 CPU”，但利于平稳恢复

---

## IS-IS（isisd）调优重点

### 1) SPF 节流（强烈推荐）
- 选项 A：最小 SPF 间隔
  - spf-interval [level-1|level-2] (1–120) 秒
- 选项 B：IETF SPF backoff 算法（粒度更细）
  - spf-delay-ietf init-delay/short-delay/long-delay/holddown/time-to-learn (0–60000ms)
- 建议
  - 首选启用 spf-delay-ietf，示例：init 200 short 500 long 5000 holddown 10000 learn 1000
  - 或仅设 spf-interval：2–5s（更抑峰，收敛更慢）
- 依据
````c path=isisd/isis_cli.c mode=EXCERPT
"spf-interval [level-1|level-2] (1-120)"
"spf-delay-ietf init-delay (0-60000) short-delay (0-60000) ..."
````
<augment_code_snippet path="isisd/isis_spf.c" mode="EXCERPT">
```c
if (area->spf_delay_ietf[level - 1]) {
  long delay = spf_backoff_schedule(...);
  event_add_timer_msec(..., delay, ...);
  return ISIS_OK;
}
```
</augment_code_snippet>

### 2) LSP 生成/刷新/寿命（抑制洪泛频率）
- 命令（进程级）
  - lsp-gen-interval [l1|l2] (1–120) s
  - lsp-refresh-interval [l1|l2] (1–65235) s
  - max-lsp-lifetime [l1|l2] (350–65535) s
- 建议（初建/大规模变更期）
  - lsp-gen-interval 提高到 5–10s
  - refresh-interval 用默认或加大（视规模）
- 依据
````text path=doc/user/isisd.rst mode=EXCERPT
.. clicmd:: lsp-gen-interval [level-1 | level-2] (1-120)
.. clicmd:: lsp-refresh-interval [level-1 | level-2] (1-65235)
.. clicmd:: max-lsp-lifetime [level-1 | level-2] (350-65535)
````

### 3) 邻接/数据库同步节奏（接口/全局）
- 命令
  - isis hello-interval [l1|l2] (1–600) s；isis hello-multiplier (2–100)
  - isis csnp-interval (1–600) [l1|l2]
  - isis psnp-interval (1–120) [l1|l2]
- 建议
  - 初建期可适度增大 csnp/psnp-interval（如 20/10s）以减洪泛频率；hello 维持默认更利于收敛
- 依据
````text path=doc/user/isisd.rst mode=EXCERPT
.. clicmd:: isis csnp-interval (1-600) [level-1 | level-2]
.. clicmd:: isis psnp-interval (1-120) [level-1 | level-2]
.. clicmd:: isis hello-interval ... hello-multiplier ...
````

### 4) Overload-bit（强烈推荐：启动保护）
- 命令（进程级）
  - set-overload-bit
  - set-overload-bit on-startup (0–86400)
- 作用
  - 启动/收敛期不作为转发中间节点，给路由计算“缓冲时间”，避免拓扑未稳先承载流量
- 参考设置
  - set-overload-bit on-startup 60–300
- 依据
````c path=isisd/isis_cli.c mode=EXCERPT
DEFPY_YANG(set_overload_bit, "[no] set-overload-bit", ...)
DEFPY_YANG(set_overload_bit_on_startup, "set-overload-bit on-startup (0-86400)$val", ...)
````

### 5) 其他
- lsp-mtu (128–4352)：按网络一致性配置即可；非 CPU 关键项
- Three-way handshake：默认启用，保证 P2P 邻接健壮性
- FRR（LFA/TI‑LFA）：初建阶段如需降负，可先用 fast-reroute priority-limit 限制计算范围或暂缓开启大规模 FRR 计算
````text path=doc/user/isisd.rst mode=EXCERPT
.. clicmd:: fast-reroute priority-limit [critical | high | medium] [level-1 | level-2]
````

---

## 建议参数组合（示例）

- OSPFv3 初建/大规模注入期（更平滑）
  - timers throttle spf 200 1000 10000
  - timers lsa min-arrival 1000
  - write-multiplier 15（或维持默认 20）
  - 接口 hello/dead/retransmit/transmit-delay 保持默认（10/40/5/1）

- IS-IS 初建/大规模注入期（更平滑）
  - spf-delay-ietf init 200 short 500 long 5000 holddown 10000 time-to-learn 1000
    （或 spf-interval level-1 3 / level-2 3）
  - lsp-gen-interval level-1 5 / level-2 5
  - csnp-interval level-1 20 / level-2 20；psnp-interval level-1 10 / level-2 10
  - set-overload-bit on-startup 120
  - hello/multiplier 维持默认以保证邻接建立速度

注意
- 增大延时/间隔会降低 CPU 峰值，但也会拉长收敛时间；请按“峰值 CPU、收敛时延、链路稳定性”平衡微调。
- BFD 会提升故障检测速度但会引入额外事件压力；初建期可暂缓在全网启用。
- 以上为通用起点；最佳值依赖邻接规模、设备 CPU/内核、LFA/SR 使用情况。建议先在一两个节点 A/B 验证。

如果你提供邻居/路由规模、设备型号/核心数、目标收敛窗口（例如 60–180 秒）、是否启用 FRR/SR/BFD，我可以给出更贴合的参数落点与逐步验证清单。
