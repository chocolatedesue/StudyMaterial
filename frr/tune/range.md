## 约定
- ms = 毫秒
- s = 秒
- bytes = 字节
- count = 计数（无单位的数量/倍数）

## Zebra（数据面/路由内核交互）
- zebra work-queue: 毫秒（ms）
  - 含义：RIB 工作队列的 hold 时间
  - 默认 10 ms；范围 0–10000 ms

- zebra zapi-packets: 计数（count）
  - 含义：主线程每轮处理的 ZAPI 包数量上限
  - 默认 1000；范围 1–10000

- zebra kernel netlink batch-tx-buf <size> <threshold>: 字节（bytes）
  - 含义：Netlink 批量发送缓冲大小与触发阈值
  - 默认 size 131072、threshold 122880；范围 1–1048576

- zebra --nl-bufsize: 字节（bytes）
  - 含义：Netlink 接收缓冲（SO_RCVBUF）
  - 默认 131072；范围依内核限制（建议≥262144）

- zebra dplane limit: 计数（count）
  - 含义：dataplane 未处理更新的队列上限（软限额/观测）
  - 默认 200；范围 0–10000

- zebra nexthop-group keep: 秒（s）
  - 含义：NHG 结构的保留时间
  - 默认 180 s；范围 1–3600 s

## OSPFv3（ospf6d）
- timers throttle spf <delay> <initial-hold> <max-hold>: 毫秒（ms）
  - 自适应 SPF 节流三元组
  - 范围各 0–600000 ms

- timers lsa min-arrival: 毫秒（ms）
  - 同一 LSA 的最小到达间隔
  - 范围 0–600000 ms

- write-multiplier: 计数（count）
  - 每次写线程处理的接口数上限
  - 默认 20；范围 1–100

- 接口 hello-interval: 秒（s）
  - 默认 10；范围 1–65535

- 接口 dead-interval: 秒（s）
  - 默认 40；范围 1–65535

- 接口 retransmit-interval: 秒（s）
  - 默认 5；范围 1–65535

- 接口 transmit-delay: 秒（s）
  - 默认 1；范围 1–3600

- 接口 graceful-restart hello-delay: 秒（s）
  - 默认 10；范围未文档限制（一般按需要设置）

-（可选）OSPFv3 外部汇总 aggregation timer: 秒（s）
  - 默认 5；范围 5–1800

## IS-IS（isisd）
- spf-interval [level-1|level-2]: 秒（s）
  - 最小 SPF 间隔
  - 范围 1–120 s

- spf-delay-ietf init/short/long/holddown/time-to-learn: 毫秒（ms）
  - IETF SPF 回退算法的 5 个参数
  - 各 0–60000 ms

- lsp-gen-interval [L1|L2]: 秒（s）
  - LSP 最小重生成间隔
  - 范围 1–120 s

- lsp-refresh-interval [L1|L2]: 秒（s）
  - LSP 刷新间隔
  - 范围 1–65235 s

- max-lsp-lifetime [L1|L2]: 秒（s）
  - LSP 最大生命周期
  - 范围 350–65535 s

- isis csnp-interval [L1|L2]: 秒（s）
  - 范围 1–600 s

- isis psnp-interval [L1|L2]: 秒（s）
  - 范围 1–120 s

- isis hello-interval [L1|L2]: 秒（s）
  - 范围 1–600 s

- isis hello-multiplier [L1|L2]: 倍数（unitless）
  - Dead/Hold 时间 = hello-interval × multiplier
  - 范围 2–100

- lsp-mtu: 字节（bytes）
  - 范围 128–4352

- set-overload-bit on-startup: 秒（s）
  - 启动阶段的 overload 持续时间
  - 范围 0–86400 s

如果你需要，我可以把你当前配置中的这些值解析出来，对照单位和默认/范围给一份“启动阶段 vs 稳态阶段”的对比清单，方便直接套用。
