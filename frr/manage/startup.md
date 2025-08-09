我先打开并阅读 tools/frrcommon.sh.in 文件，以便梳理其中的整体结构与执行流程。

## 脚本概览（tools/frrcommon.sh.in）

这是 FRR 其他脚本复用的“公共库”，主要封装了各守护进程（daemons）的启动/停止/状态查询逻辑。它不直接执行动作；被调用方需要预先定义以下日志函数：
- log_success_msg
- log_warning_msg
- log_failure_msg

同时它会加载 FRR 的配置（/etc/frr/daemons 等），若该主配置缺失会直接退出。

如果你指的是别的脚本，请告诉我具体路径；下文梳理的就是 tools/frrcommon.sh.in 的逻辑。


## 路径与关键变量

- FRR_PATHSPACE：命名空间后缀，来自 watchfrr（用于多路径空间部署）
  - suffix: 可用于拼接到配置/运行目录
  - nsopt: 传入各二进制的 -N 参数
- 路径常量：
  - D_PATH: 守护进程二进制目录（如 /usr/lib/frr）
  - C_PATH: 配置目录（如 /etc/frr）
  - V_PATH: 运行状态目录（如 /var/run/frr）
  - B_PATH: 常规 bin
  - VTYSH: vtysh 二进制路径
- 权限/用户组：
  - FRR_USER, FRR_GROUP, FRR_VTY_GROUP, FRR_CONFIG_MODE
- 其他：
  - DAEMONS：有序的守护进程列表（zebra 必须第一；watchfrr 不在列表中）
  - RELOAD_SCRIPT：frr-reload.py
  - FRR_DEFAULT_PROFILE：默认 profile（traditional/datacenter）


## 工具函数

- is_user_root
  - 检查是否 root 执行；若设置 FRR_NO_ROOT=yes 则跳过检查
- debug
  - 打印带时间戳与参数的调试日志（需设置 watchfrr_debug 才输出）
- vtysh_b [daemon?]
  - 若 /etc/frr/frr.conf 存在：调用 vtysh -b（必要时加 -d 指定 daemon）应用配置
  - 若参数是 watchfrr，直接跳过
- daemon_inst dmninst
  - 解析 “守护进程名-实例名” 形式为 daemon 和 inst（实例名可空）
- daemon_list enabled_var disabled_var
  - 根据 DAEMONS 和 daemons 配置（含 ${daemon}_instances）生成启/停列表
  - 特例：zebra/staticd/mgmtd 无论配置如何都视为启用（cfg=yes）
  - 会调用 daemon_prep 做预检查/准备
- daemon_prep daemon inst
  - 检查二进制是否存在；若 /etc/frr/frr.conf 不存在，则确保每守护进程对应的 cfg 文件存在（无则以正确 owner/group/mode 创建空文件）
- daemon_status dmninst
  - 根据 pidfile 判断运行状态（0 运行中，1 未运行，3 无 pidfile）
- print_status dmninst
  - 包装 daemon_status 并打印日志


## 个别守护进程操作

- daemon_start [--all] dmninst
  - 需 root（或 FRR_NO_ROOT=yes）
  - 设置 MAX_FDS（ulimit -n），调用 daemon_prep，确保 V_PATH 存在并权限正确
  - 读取 ${daemon}_wrap 和 ${daemon}_options 以及实例选项 -n
  - 拼出命令并执行：$all_wrap $wrap $bin $nsopt -d $frr_global_options $instopt $args
  - 成功后：
    - 如果是 --all 模式：先不调用 vtysh（等全部启动完再一次性调用）
    - 单启动：立即 vtysh_b "$daemon"
- daemon_stop dmninst [--quiet|--reallyall]
  - 需 root（或 FRR_NO_ROOT=yes）
  - 找 pidfile，读取 pid，kill -2（SIGINT），每 0.1s 轮询一次，最多约 120 秒
  - 成功则删除 pidfile；失败会记录 still_running=1 并返回失败


## 批量操作

- all_start
  - 根据 daemon_list 得到实际要启动的条目（包含多实例）
  - 依序调用 daemon_start --all
  - 全部完成后再统一 vtysh_b（应用配置）
- all_stop [--reallyall]
  - 先计算启用/禁用列表；--reallyall 时把禁用的也纳入停止
  - 反向顺序停止（reverse），每个后台执行，最后 wait 全部结束
- all_status
  - 对所有（启用）守护进程调用 print_status，聚合结果


## 配置加载与兼容

- 首先要求 C_PATH/daemons 必须存在（否则退出）
- 加载 C_PATH/daemons
- 若未设置 FRR_PATHSPACE，再加载历史/兼容配置（若存在且有内容）：
  - C_PATH/daemons.conf
  - /etc/default/frr
  - /etc/sysconfig/frr
  - 加载历史配置时，会把各 daemon 的开启值与新配置做“OR 合并”
- watchfrr_options 保护：
  - 若被设置为 bash 数组，忽略并给出警告
- frr_profile 自动判定：
  - 若 /etc/cumulus 存在：datacenter
  - 否则用 FRR_DEFAULT_PROFILE（若存在）
  - 若最终有 profile，则在 frr_global_options 中添加 -F 参数


## 统一调度入口

- frrcommon_main cmd [args...]
  - 如果 args 是 “all” 或为空：走批量分支
    - start → all_start
    - stop → all_stop
    - restart → all_stop --quiet 然后 all_start
    - 其他 → 直接执行同名函数（$cmd "$@"）
  - 如果 args 指定了具体的 dmninst（如 bgpd 或 bgpd-1）：走单实例分支
    - start → daemon_start
    - stop → daemon_stop
    - restart → 先 stop 再 start
    - 其他 → 直接执行同名函数（$cmd "$@"）


## 典型流程示意

- 启动全部
  1) frrcommon_main start
  2) all_start → 遍历启用的守护进程按顺序调用 daemon_start --all
  3) 全部启动完后调用 vtysh_b 统一应用配置

- 启动单个
  1) frrcommon_main start bgpd
  2) daemon_start → 成功后立即 vtysh_b bgpd

- 停止全部
  1) frrcommon_main stop
  2) all_stop → 反向顺序并行停止，wait 等待完成

- 状态查询
  1) frrcommon_main status
  2) all_status → 逐个 daemon_status，打印结果


## 依赖/约定的配置项（通常在 /etc/frr/daemons 中）

- 每个守护进程的开关变量：zebra, bgpd, …（值非空且非“no/0”即视为启用）
- 多实例：${daemon}_instances，例如 “bgpd_instances=red,blue”
- 守护进程参数：${daemon}_options
- 守护进程外部包装：${daemon}_wrap（如用前置包装命令/脚本）
- 全局选项：frr_global_options（脚本会在启动命令中拼接）
- frr_profile（若未设置会自动推断）
- watchfrr_options（避免设置为 bash 数组）

需要我把该逻辑画一张简单时序/流程图，或者进一步对某一个函数做更细的逐行解读吗？
