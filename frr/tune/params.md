## 目标与思路
你要“减缓建立拓扑带来的计算开销”（即初始收敛/大规模路由灌入时的 CPU 峰值与抖动）。在 zebra 层，最直接能调节“批处理/节流/缓冲”的项主要是：
- RIB 工作队列的 hold 时间（批处理节流）
- ZAPI 每次处理的包数（主线程让出前的工作量）
- Dataplane 入队上限（软限额/观测）
- 内核 Netlink 批量发送缓冲（批量刷写至内核）
- Nexthop‑Group 保留时间（结构复用，减少反复创建/销毁）
- 递归使用备份下一跳（更偏收敛策略；对 CPU 影响次要）

下面列出每项的默认值、可调范围、位置依据，并标出“对降低初始开销”的重要程度。

## 关键参数与默认/范围

- zebra work-queue（RIB 工作队列 hold，毫秒）
  - 作用：增大可批处理窗口，降低事件风暴下的 SPF/RIB/FIB 交替计算频率与上下文切换
  - 默认值：10 ms
  - 范围：0–10000 ms
  - 命令（全局配置）：zebra work-queue <0-10000>
  - 重要性：高（平滑峰值最有效的旋钮之一）
  - 代码依据：
````c path=zebra/zebra_router.h mode=EXCERPT
    #define ZEBRA_RIB_PROCESS_HOLD_TIME 10
````
    <augment_code_snippet path="zebra/zebra_vty.c" mode="EXCERPT">
    ```c
    DEFUN_HIDDEN (zebra_workqueue_timer, "zebra work-queue (0-10000)", ...)
    ```
    </augment_code_snippet>

- zebra zapi-packets（主线程在让出前处理的 ZAPI 包数量）
  - 作用：控制主线程单位时间处理量；越大吞吐越高但更“顶 CPU”，越小更频繁让出、抑制尖峰
  - 默认值：1000
  - 范围：1–10000
  - 命令（全局配置）：zebra zapi-packets <1-10000>
  - 重要性：中‑高（与 work‑queue 配合，平滑主线程负载）
  - 代码依据：
````c path=zebra/zebra_router.h mode=EXCERPT
    #define ZEBRA_ZAPI_PACKETS_TO_PROCESS 1000
````
    <augment_code_snippet path="zebra/zebra_vty.c" mode="EXCERPT">
    ```c
    DEFUN_HIDDEN (zebra_packet_process, "zebra zapi-packets (1-10000)", ...)
    ```
    </augment_code_snippet>

- zebra dplane limit（dataplane 入队待处理更新的“队列上限”）
  - 作用：限制/观测 dataplane 未处理队列深度；当前实现更偏“软限额/可视化”，未见硬性丢弃路径
  - 默认值：200
  - 范围：0–10000（no zebra dplane limit 恢复默认）
  - 命令（全局配置）：zebra dplane limit <0-10000>
  - 重要性：中（容量管理/观察；对“减负”影响间接）
  - 代码依据：
````c path=zebra/zebra_dplane.c mode=EXCERPT
    const uint32_t DPLANE_DEFAULT_MAX_QUEUED = 200;
    void dplane_set_in_queue_limit(uint32_t limit, bool set) { ... }
````
    <augment_code_snippet path="zebra/zebra_vty.c" mode="EXCERPT">
    ```c
    DEFUN (zebra dplane limit (0-10000), ...)  // no ... 恢复默认
    ```
    </augment_code_snippet>

- zebra kernel netlink batch-tx-buf（Linux，内核路由编程批量发送缓冲）
  - 作用：扩大批量刷写缓冲/阈值，减少 syscall 次数、提升灌入吞吐（代价是更大一次性批次）
  - 默认值：缓冲 131072 字节（128 KB），发送阈值 122880 字节（120 KB）
  - 范围：1–1048576（1 MB）
  - 命令（全局配置，隐藏）：zebra kernel netlink batch-tx-buf <1-1048576> <1-1048576>
  - 重要性：高（大规模一次性写内核时，很有效）
  - 代码依据：
````c path=zebra/kernel_netlink.c mode=EXCERPT
    #define NL_DEFAULT_BATCH_BUFSIZE (16 * NL_PKT_BUF_SIZE)  // 16*8192=131072
    #define NL_DEFAULT_BATCH_SEND_THRESHOLD (15 * NL_PKT_BUF_SIZE) // 122880
    DEFUN_HIDDEN("zebra kernel netlink batch-tx-buf (1-1048576) (1-1048576)", ...)
````

- Nexthop‑Group 保留时间（nhg keep，秒）
  - 作用：更久地保留 NHG 以复用，减少频繁创建/销毁导致的内核/用户态开销
  - 默认值：180 s
  - 范围：1–3600 s（no 恢复默认）
  - 命令（全局配置）：zebra nexthop-group keep <1-3600>
  - 重要性：中（建拓扑期/抖动时有帮助）
  - 代码依据：
````c path=zebra/zebra_router.h mode=EXCERPT
    #define ZEBRA_DEFAULT_NHG_KEEP_TIMER 180
````
    <augment_code_snippet path="zebra/zebra_vty.c" mode="EXCERPT">
    ```c
    DEFPY (zebra nexthop-group keep (1-3600), ...)
    ```
    </augment_code_snippet>

- 递归解析时使用备份下一跳（resolve‑via‑backup）
  - 作用：允许递归解析时利用备份 NH，提升切换连贯性（对 CPU 影响次要）
  - 默认：启用（true）
  - 开关：zebra nexthop resolve-via-backup / no zebra nexthop resolve-via-backup
  - 重要性：低‑中（更多是收敛策略；不是主力“降负”旋钮）
  - 代码依据：
````c path=zebra/zebra_nhg.c mode=EXCERPT
    static bool use_recursive_backups = true; // default on
````

- 启动参数（非 vty 配置）
  - -s, --nl-bufsize BYTES（Linux Netlink 接收缓冲）
    - 默认：128 KB
    - 范围：任意正整数（内核上限受限）；建议 ≥256 KB 以应对读风暴
    - 重要性：中（防丢包/阻塞；与 batch‑tx‑buf互补）
    - 代码依据：
````c path=zebra/main.c mode=EXCERPT
      uint32_t rcvbufsize = 128 * 1024; // default
````

- 内部 dataplane 每周期新工作量（不可在 vty 配）
  - 默认：100（每循环最大处理新更新数，平衡公平性/吞吐）
  - 说明：目前无 vty 直接调节项（用于内部节流）
  - 代码依据：
````c path=zebra/zebra_dplane.c mode=EXCERPT
    const uint32_t DPLANE_DEFAULT_NEW_WORK = 100;
````

## 哪些参数更重要（面向“降低建拓扑开销”）

优先级（从大到小）：
1) zebra work-queue：把 RIB 处理批量化。建议在拓扑初建阶段适度增大，如 50–200 ms，显著降低 CPU 峰值与线程切换；稳定后可调回较小值。
2) kernel netlink batch-tx-buf：扩大到 256–512 KB 缓冲、相应阈值（如 262144 / 196608 或 524288 / 458752），减少内核交互次数，提高一次性写入吞吐。
3) zebra zapi-packets：为平滑 CPU，可适度降低到 500 左右，增加调度让出频率（更平滑但用时略长）；若希望更快完成，反之可增大（但更“顶 CPU”）。
4) nexthop-group keep：可提高到 300–600 s，增大结构复用率，降低频繁的 NHG 创建/销毁；占用内存稍增。
5) 启动 -s nl-bufsize：建议 ≥ 256 KB（根据内核与规模可 512 KB+），避免高峰期 netlink 接收拥塞。
6) zebra dplane limit：更偏可视化/软限额；一般保持默认 200 即可。除非需要容量监控/测试，不建议过度调整。

## 建议的“降负”参考组合（示例）

- 初次建拓扑/大规模路由灌入阶段（平滑优先）
  - zebra work-queue 100
  - zebra zapi-packets 500
  - zebra kernel netlink batch-tx-buf 262144 196608
  - zebra nexthop-group keep 600
  - 启动参数：-s 262144（或更高，结合系统限制）
- 稳定后（延迟优先）
  - zebra work-queue 10–50
  - zebra zapi-packets 1000（默认）或略高
  - kernel batch 可保留较大值（对稳定影响小）

注意
- 以上为通用起点，最佳值依赖 CPU/内核版本/路由规模/ECMP/邻表规模等，建议按“CPU 峰值、收敛时延、内核 netlink 统计”进行 A/B 微调。
- batch 设置过大可能导致“少量大批次”的抖动；观察 show zebra dplane / 内核软中断/调度延迟统计划分批增改。
- “zebra dplane limit”当前代码未见硬性拒绝逻辑，作为上限告警/观测更合适；若严格限流需要外部编排/上游协议节流配合。

如果你能提供设备型号/CPU、内核版本、一次灌入的典型路由量级、目标时间窗（如 1–3 分钟完成灌入且 CPU 平稳），我可以给出更贴合的参数落点与一步步验证方法。
