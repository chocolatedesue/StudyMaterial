I’ll scan docs for exact value constraints of the commands used (hello timers, SPF IETF delay, lsp-gen-interval, is-type, topology, metric-style) to provide accurate ranges and types. 我会在不超出现有示例的前提下，给你“单实例 + 仅 IPv6 + 适合网格拓扑 + 快速收敛”的模板，并标注每个配置项的类型与取值范围（均来自本仓库中的示例与文档）。

Checklist
- 单实例 IS-IS 配置模板（仅 IPv6）
- 接口模板（P2P，快速收敛）
- 参数项的类型与取值范围
- 网格批量化命名与占位说明

## 路由进程模板（仅 IPv6，L1-only，快速收敛）

参考位置
- tests/topotests/isis_sr_topo1/rt1/isisd.conf（IPv6+L1+模板基准）
- doc/user/isisd.rst（is-type、metric-style、lsp-gen-interval、hello 定时、LFA 等取值范围）

示例
- 将 INSTANCE、AREA、SYSID、LOOPBACK 替换成你的网格节点值

```
hostname R-<ROW>-<COL>
password 1
log file isisd.log
!
interface lo
 ipv6 address <LOOPBACK>/128
 ipv6 router isis INSTANCE
 isis passive
!
router isis INSTANCE
 net 49.<AREA>.<SYSID>.00
 is-type level-1
 metric-style wide
 topology ipv6-unicast
 lsp-gen-interval 2
!
```

说明
- 仅使用本仓库示例中出现过的项：router isis、net、is-type、metric-style、topology ipv6-unicast、lsp-gen-interval、接口上的 ipv6 router isis/isis passive。
- 不引入 SR、spf-delay-ietf、TE 等未在你给定基准文件中使用的项。

## 接口模板（P2P 链路，快速收敛）

参考位置
- tests/topotests/isis_sr_topo1/rt1/isisd.conf（hello 定时）
- doc/user/isisd.rst（hello 取值范围、接口下命令）

示例
```
interface <if-name>
 ipv6 address <LINK-PFX>::<ID>/64
 ipv6 router isis INSTANCE
 isis network point-to-point
 isis hello-interval 1
 isis hello-multiplier 5
 isis metric 10
!
```

建议
- 网格统一度量值便于等价负载分担：isis metric 10
- 快速失效探测：1 秒 Hello × 5（5 秒 down）；根据稳定性可在 3–10 间选择
- 所有链路为点到点：isis network point-to-point

## 配置项类型与取值范围

基于 isisd.rst 中的 CLICMD 声明与本仓库示例，列出你模板用到的指令参数范围与类型。

- router isis INSTANCE
  - 类型：字符串（进程名/ID），示例用 “1” 或 “INSTANCE”
  - 备注：进程名在设备内唯一（无范围数值限制的声明，按 WORD 处理）

- net 49.<AREA>.<SYSID>.00
  - 类型：ISO NET 地址字符串（Area + System-ID + NSEL）
  - 备注：示例格式如 49.0000.0000.0000.0001.00（tests/topotests/isis_sr_topo1/rt1/isisd.conf）
  - 要求：SYSID 全网唯一；NSEL 固定 00

- is-type
  - 语法与范围：is-type [level-1 | level-1-2 | level-2-only]（doc/user/isisd.rst: “.. clicmd:: is-type …”）
  - 类型：枚举
  - 建议：网格域内使用 level-1

- metric-style
  - 语法与范围：metric-style [narrow | transition | wide]（doc/user/isisd.rst）
  - 类型：枚举
  - 建议：wide（与接口 isis metric 的高范围匹配）

- topology
  - 使用值：topology ipv6-unicast（tests/topotests/isis_sr_topo1/rt1/isisd.conf）
  - 类型：枚举（本模板仅使用 ipv6-unicast）

- lsp-gen-interval
  - 语法与范围：lsp-gen-interval [level-1 | level-2] (1-120)（doc/user/isisd.rst）
  - 类型：整数（秒）
  - 示例：lsp-gen-interval 2（在 rt1 示例中已出现）

- 接口命令：ipv6 router isis INSTANCE
  - 类型：开关（启用接口加入该 IS-IS 实例进行 IPv6 邻接和前缀发布）

- 接口命令：isis network point-to-point
  - 类型：枚举值（本模板使用 point-to-point，示例中已出现）

- 接口命令：isis hello-interval
  - 语法与范围：isis hello-interval [level-1 | level-2] (1-600)（doc/user/isisd.rst）
  - 类型：整数（秒）
  - 示例：1

- 接口命令：isis hello-multiplier
  - 语法与范围：isis hello-multiplier [level-1 | level-2] (2-100)（doc/user/isisd.rst）
  - 类型：整数（倍数）
  - 示例：5 或 10

- 接口命令：isis metric
  - 语法与范围：isis metric [level-1 | level-2] [(0-255) | (0-16777215)]（doc/user/isisd.rst）
  - 类型：整数
  - 说明：在 metric-style wide 下可用 0–16777215；在 narrow/transition 下为 0–255
  - 示例：10

- 接口命令：isis passive
  - 类型：标志（无参数；在 Loopback 上常用）

注：以上范围与类型均来自本仓库文档/示例；未引用文档中未出现或外部资料项。

## 网格批量化占位与分配建议（不引入新指令）

- 实例名：统一 “1” 或 “ISIS”
- AREA：建议统一，如 0000.0000.0000
- SYSID：按节点行列映射成唯一 12 位十六进制（例如 0000.0000.00A1）
- Loopback：2001:db8:<grid-id>::N/128
- 链路前缀：每条边分配一个 /64，接口地址末尾使用 ::1/::2

需要我基于你网格的规模（行/列）、接口命名约定与前缀规划，生成整套 isisd.conf 批量文件吗？我会严格用上述指令与范围，不添加仓库示例之外的配置。