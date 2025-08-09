I’m going to quickly scan this repository to locate where mgmtd (management daemon) and staticd are configured by default (e.g., in /etc/frr/daemons templates, build-time flags, or systemd/init scripts). This will let me explain their configurable items and whether they can be disabled by default in this fork.

I’ll search within the repository for mgmtd’s manpage and options to list its configurable flags and how it integrates with staticd and others.

I'll look up the MGMTD_VTY_PORT constant to report its default VTY port.

## 概览：MGMTd 与 staticd 是什么

- MGMTd（Management Daemon）
  - 作用：FRR 的集中管理面（Management Plane）守护进程，统一接入各种前端（CLI/Netconf/Restconf/gRPC 等），基于 YANG 的 northbound 接口与各路由守护进程协同，提供集中化的配置与状态访问。
  - 当前已提供集中化 CLI（对已迁移的守护进程），未来可扩展到 RESTCONF/NETCONF 等。
- staticd
  - 作用：管理静态路由（ip route / ipv6 route 等）的独立守护进程。现代 FRR 下静态路由功能基本由 staticd 提供（而不是 zebra 直接处理）。

参考（仓库内文档/代码）：
- 用户文档：doc/user/mgmtd.rst
- 通用命令行选项：doc/manpages/common-options.rst
- 运行脚本和模板：tools/frr.in、tools/etc/frr/daemons、tools/frr.service.in
- mgmtd 主程序：mgmtd/mgmt_main.c、mgmtd/mgmt_vty.c


## 重要配置项（运行时）

- /etc/frr/daemons 文件：决定哪些守护进程启动，以及它们的默认 VTY 监听地址/端口等
  - mgmtd、staticd 都有对应的 “_options”，可设置 VTY 监听地址(-A)等
  - 设为 yes/no 控制是否启动（常见发行版默认全部是 no，由管理员按需启用）
- 常见通用选项（适用于 mgmtd/staticd 等所有 FRR 守护进程，见 common-options.rst）
  - -A, --vty_addr：VTY 监听地址（建议 127.0.0.1 或 ::1）
  - -P, --vty_port：VTY 端口；设为 0 可禁用 TCP VTY
  - -f：配置文件路径；-C：仅校验配置后退出；-i：自定义 pid 文件路径
  - -u/-g：切换运行用户/组；--vty_socket：VTY Unix socket 目录；-N：pathspace 逻辑隔离等
- mgmtd 特有/额外选项（见 mgmtd/mgmt_main.c）
  - --socket_size/-s：设置 mgmtd 对等连接的发送缓冲尺寸
  - -n（已废弃）：使用 NetNS 作为 VRF backend，提示改用全局 -w
  - 其它通用选项通过 libfrr 的 frr_preinit/frr_opt_add 注入（如 -A/-P/-u/-g 等）

示例（模板中的 mgmtd/staticd 选项行）：
````sh path=tools/etc/frr/daemons mode=EXCERPT
vtysh_enable=yes
mgmtd_options="  -A 127.0.0.1"
staticd_options="-A 127.0.0.1"
````

mgmtd 提供的集中 CLI（示例命令定义）：
````c path=mgmtd/mgmt_vty.c mode=EXCERPT
DEFPY(mgmt_edit, mgmt_edit_cmd,
      "mgmt edit {create|delete|merge|replace|remove}$op XPATH [json|xml]$fmt [lock$lock] [commit$commit] [DATA]",
      MGMTD_STR ...)
````


## 重要配置项（构建时）

- configure 选项可在编译期启用/禁用各守护进程
  - mgmtd：默认启用；可用 --disable-mgmtd 关闭（configure.ac 中 enable_mgmtd != "no" 才启用）
  - staticd：FRR 通常支持按守护进程编译开关（与 mgmtd 同模式），一般可用 --disable-staticd 关闭
- mgmtd 还支持本地校验开关：--enable-mgmtd-local-validations

参考（构建条件）：
````m4 path=configure.ac mode=EXCERPT
AS_IF([test "$enable_mgmtd" != "no"], [
  AC_DEFINE([HAVE_MGMTD], [1], [mgmtd])
])
AM_CONDITIONAL([MGMTD], [test "$enable_mgmtd" != "no"])
````


## 与其它组件的集成关系

- mgmtd 会链接各守护进程的 YANG/CLI 模块，通过 northbound 完成集中管控
  - 例如对 staticd 的集成：
    - mgmtd/mgmt_main.c 在编译检测到 HAVE_STATICD 时，会加载 staticd 的 CLI/YANG 信息
- 若禁用 mgmtd，FRR 可回退至传统的 per-daemon VTY 模式（vtysh 连接各守护进程 socket）；但 mgmtd 的集中式“mgmt …”命令将不可用
- 若禁用 staticd，静态路由相关配置将不可用（你的配置中若存在静态路由，将失效）


## 是否可以默认关闭 mgmtd 和 staticd？

结论：可以，且对大多数不需要集中化 YANG 管理或静态路由的场景是合理的默认。

- 关闭 mgmtd 的影响
  - 不再提供集中 YANG/CLI“mgmt …”接口；但传统 vtysh（连接各守护进程）仍可用
  - 如果你没有使用 NETCONF/RESTCONF/gNMI/集中式事务等新式工作流，默认关闭 mgmtd 通常更简单、安全（减少面暴）
- 关闭 staticd 的影响
  - 不能配置/下发静态路由；若你的配置里包含“ip route/ipv6 route”，这些将不生效
  - 如果你的网络完全依赖动态路由协议，且明确不需要静态路由，可以默认关闭

建议的默认策略：
- 服务器/设备不需要静态路由和集中化 YANG 管理：默认禁用 mgmtd 与 staticd
- 需要静态路由但不使用 mgmtd：启用 staticd，禁用 mgmtd
- 需要集中管理（NETCONF/RESTCONF/gRPC 或统一事务/锁/回滚）：启用 mgmtd（可选同时启用 staticd 根据需求）


## 如何默认关闭（运维层）

- 运行时（系统安装后）
  - 在 /etc/frr/daemons 中设置：
    - mgmtd=no
    - staticd=no
  - 保留或调整 mgmtd_options/staticd_options 的 -A/-P 等以便需要时再启用
- 构建时（发行/打包默认）
  - 配置阶段传入：
    - --disable-mgmtd
    - --disable-staticd（若需要）
  - 以及提供默认的 /etc/frr/daemons 模板，将 mgmtd、staticd 置为 no

提示：
- 本仓库的样例 daemons 文件中给出了 mgmtd_options/staticd_options 行，你可以基于它们生成自己的默认模板，将对应守护进程置为 no 即可。
- Systemd 服务 tools/frr.service.in 通过 frrinit.sh 启动，frrinit.sh 会读取 /etc/frr/daemons 的 yes/no 状态决定是否启动每个守护进程。


## 风险与注意点

- 若现网配置中已有静态路由，禁用 staticd 会导致路由丢失（中断流量）
- 若已有自动化/上层系统依赖 mgmtd（YANG 事务、锁、回滚或集中接口），禁用 mgmtd 会中断管理平面
- VTY 端口对外监听请务必绑定到回环地址（-A 127.0.0.1 或 ::1）或直接 -P 0 禁用 TCP VTY，仅通过 vtysh 使用


## 相关文件快速定位

- /etc/frr/daemons 模板（默认选项与启停）：
````sh path=tools/etc/frr/daemons mode=EXCERPT
# The watchfrr, zebra and staticd daemons are always started.
...
mgmtd_options="  -A 127.0.0.1"
staticd_options="-A 127.0.0.1"
````

- mgmtd 主程序（选项/VTY/模块）：
````c path=mgmtd/mgmt_main.c mode=EXCERPT
frr_opt_add("s:n" DEPRECATED_OPTIONS, longopts,
    "  -s, --socket_size  ...\n"
    "  -n, --vrfwnetns    ...\n");
````

如果你希望我在这个仓库里把默认模板或构建参数改成“默认关闭 mgmtd 和 staticd”，告诉我你的目标发行方式（打包/源码安装），我可以准备最小改动并附带测试建议。
