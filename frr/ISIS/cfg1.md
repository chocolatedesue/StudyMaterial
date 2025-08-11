I’ll search the user docs to verify which additional convergence-related IS-IS commands exist and are documented, then summarize each option and its effect. 我来严格核对“未提到的、与收敛加速相关”的 IS-IS 配置项是否在本仓库存在，并给出作用、类型与取值范围；仅引用仓库自带文档与示例。

Checklist
- 列举站内已文档化的收敛相关命令：存在性、作用、范围/类型
- 列举实例中出现但未在用户文档标注范围的命令：存在性与作用，范围未知

## 已文档化并影响收敛的选项（确认存在）

isisd.rst

- lsp-gen-interval
  - 位置/存在性: isisd.rst “.. clicmd:: lsp-gen-interval …”
  - 作用: 同一 LSP 的最小再生成间隔（秒）；减小可更快泛洪变化
  - 类型与范围: 整数秒；(1–120)
  - 作用域: [level-1 | level-2] 可选，或全局

- lsp-refresh-interval
  - 存在: 有
  - 作用: LSP 刷新间隔（秒）；较短有助更快更新老化信息，但会增流量
  - 类型与范围: 整数秒；(1–65235)
  - 作用域: [level-1 | level-2] 或全局

- max-lsp-lifetime
  - 存在: 有
  - 作用: LSP 最大生存期（秒）；较短可更快清除失效信息（权衡与刷新频率）
  - 类型与范围: 整数秒；(350–65535)
  - 作用域: [level-1 | level-2] 或全局

- spf-interval
  - 存在: 有
  - 作用: 连续 SPF 计算的最小间隔（秒）；越小越敏捷但 CPU 压力更大
  - 类型与范围: 整数秒；(1–120)
  - 作用域: [level-1 | level-2] 或全局

- isis csnp-interval
  - 存在: 有
  - 作用: CSNP 发送间隔（秒）；减小可更快校对数据库一致性（泛洪更积极）
  - 类型与范围: 整数秒；(1–600)
  - 作用域: [level-1 | level-2]

- isis psnp-interval
  - 存在: 有
  - 作用: PSNP 发送间隔（秒）；减小可加速缺失 LSP 的请求与收敛
  - 类型与范围: 整数秒；(1–120)
  - 作用域: [level-1 | level-2]

- isis hello-interval
  - 存在: 有
  - 作用: Hello 周期（秒）；配合 multiplier 决定邻居失效检测时间
  - 类型与范围: 整数秒；(1–600)
  - 作用域: [level-1 | level-2] 或接口/全局

- isis hello-multiplier
  - 存在: 有
  - 作用: Holdtime=hello-interval×multiplier；越小失败检测越快
  - 类型与范围: 整数；(2–100)
  - 作用域: [level-1 | level-2] 或接口/全局

- isis fast-reroute lfa …
  - 存在: 有
  - 作用: 启用 per-prefix LFA 快速重路由（链路/节点失效时无缝切换，非“SPF收敛”，但显著降低业务中断）
  - 类型与范围: 枚举/标志；基础开关 isis fast-reroute lfa [level-1 | level-2]，并有 tie-breaker、load-sharing、remote-lfa/ti-lfa 等子命令
  - 作用域: 接口级（开关），也有进程下的策略子命令
  - 相关范围:
    - tie-breaker index: 整数 (1–255)
    - remote-lfa maximum-metric: 整数 (1–16777215)

- set-overload-bit / set-overload-bit on-startup
  - 存在: 有
  - 作用: 启动阶段或手动设置 Overload 位，避免本节点在初始化未稳定时被用作中转，减少黑洞/回切抖动（稳定性相关）
  - 类型与范围:
    - set-overload-bit: 标志
    - set-overload-bit on-startup (0–86400): 启动后保持秒数

- advertise-passive-only
  - 存在: 有
  - 作用: 仅发布 passive 接口前缀，减少 LSP 体积与拓扑噪音，有助于快速稳定
  - 类型与范围: 标志

- lsp-mtu
  - 存在: 有
  - 作用: 生成 LSP 的最大大小（字节）；合理设置可减少碎片、降低重传概率
  - 类型与范围: 整数字节；(128–4352)

## 在仓库示例中出现但未在用户文档标注范围的选项（确认存在）

- spf-delay-ietf
  - 存在性: 在测试用例中通过 vtysh test_isis_tilfa_topo1.py 有命令片段：router isis 1; spf-delay-ietf init-delay 60000 short-delay 0 long-delay 0 holddown 0 time-to-learn 0）
  - 作用: IETF SPF 延迟控件（init/short/long 等），在拓扑抖动时控制 SPF 延迟曲线以平衡收敛与震荡；将延迟设为 0 可极端追求快速重算
  - 类型与参数: 多个整型毫秒参数；本仓库用户文档未标注“范围”，测试中使用值为 0 或 60000（ms）
  - 提示: 因用户文档未列出范围，建议在实验环境按测试值使用；生产需评估 CPU/震荡

注：你要求“不要用不存在的配置”。以上两类命令均可在本仓库找到证据：第一类来自 isisd.rst 的 CLICMD 定义；第二类来自 tests/topotests 的可执行示例脚本。未出现在仓库文档或示例的指令未列出。

## 小结与建议
- 想要进一步加速但保持“仅用仓库已确认项”：优先从 hello-interval/hello-multiplier、spf-interval、lsp-gen-interval、csnp/psnp-interval 入手；必要时结合 LFA。
- 如接受使用测试中已有但用户文档未列范围的项，可使用 spf-delay-ietf 做更激进的 SPF 延迟控制（基于测试脚本示例参数）。