## 概览

FRRouting（FRR）由多个守护进程组成（zebra、bgpd、ospfd、isisd、ldpd、pimd 等），通常由 watchfrr 统一监管，并通过系统服务（systemd/OpenRC/SysV）启动、停止、重载。配置通常集中在：
- /etc/frr/frr.conf（集成配置）
- /etc/frr/daemons（启用/禁用各守护进程的开关）
- vtysh 提供统一 CLI（交互与批处理）

下面按常见场景列出启动/关闭/重载 FRR 或单个子进程的工具与命令。

---

## 常见服务管理（systemd）

- 启动/停止/重启/状态
  - systemctl start frr
  - systemctl stop frr
  - systemctl restart frr
  - systemctl status frr

- 热重载（优先）
  - systemctl reload frr
  - 说明：通常会调用 frr-reload.py 根据 /etc/frr/frr.conf 对运行态做“最小变更”下发，比重启更平滑

- 查看哪些单元可用（不同发行版包装可能不同）
  - systemctl list-unit-files | grep -E 'frr|bgpd|ospfd|zebra'
  - 有的发行版还提供 per-daemon 单元，如 bgpd.service、zebra.service；若存在可单独控制：
    - systemctl restart bgpd
    - systemctl reload bgpd（若支持）

---

## 旧式/其他初始化系统

- SysV（较老的系统）
  - service frr start|stop|restart|status|reload
- OpenRC（如 Alpine）
  - rc-service frr start|stop|restart
  - rc-service frr reload（如支持）

---

## 配置热重载工具：frr-reload.py

- 作用：将 /etc/frr/frr.conf 的变更“最小影响”地下发到正在运行的各守护进程，尽量避免协议抖动
- 常用命令
  - 预检查（不下发）：frr-reload.py --test /etc/frr/frr.conf
  - 执行热更：frr-reload.py --reload /etc/frr/frr.conf
- 建议流程
  1) 编辑 /etc/frr/frr.conf
  2) frr-reload.py --test … 确认无冲突
  3) systemctl reload frr 或直接 frr-reload.py --reload …

注意：某些结构性变更（如切换地址族、删除/重建 VRF、BGP 关键标识等）可能仍需要重启对应守护进程。

---

## vtysh（统一 CLI/批处理）

- 交互式进入 CLI
  - vtysh
- 批处理下发命令
  - vtysh -c "configure terminal" -c "..." -c "..."
- 按 frr.conf 批量应用（快捷方式）
  - vtysh -b
  - 说明：读取 /etc/frr/frr.conf 并按顺序下发，适用于快速同步配置（不做“最小差异”计算）
- 保存运行配置到磁盘
  - vtysh -c "write memory"

提示：对 BGP 这类敏感协议，优先用 frr-reload.py 做最小差异热更；vtysh -b 更直接但可能引发更大范围的修改。

---

## 单个守护进程（子进程）的控制

- 通过 systemd（若提供单独单元）
  - systemctl restart bgpd
  - systemctl reload bgpd（若支持）
  - systemctl status bgpd
- 通过 watchfrr 统一管理
  - FRR 默认由 watchfrr 拉起与保活；直接 kill 子进程通常会被自动拉起
  - 要永久禁用某个守护进程：编辑 /etc/frr/daemons 将对应条目标为 no/false，然后 systemctl restart frr
- 实验/容器内直接拉起（不经 systemd）
  - 典型（示例）：
    - zebra -d -f /etc/frr/zebra.conf -A 127.0.0.1
    - bgpd  -d -f /etc/frr/bgpd.conf  -A 127.0.0.1
  - 停止：
    - pkill bgpd（或按需精确 kill 目标 PID）
  - 说明：-d 后台，-f 指定配置文件，-A 设定 VTY 监听地址

---

## /etc/frr/daemons（启停开关）

- 该文件决定哪些守护进程由服务启动时启用
  - 例如：bgpd=yes、zebra=yes、ospfd=no
- 修改后执行
  - systemctl restart frr
- 好处：可控地启用/禁用单个子进程，同时保持 watchfrr 的监管

---

## 信号与日志

- 日志轮转常见做法（依发行版 logrotate 配置而定）
  - 向守护进程发送 HUP 以重新打开日志文件（示例）
    - pkill -HUP bgpd
  - 更推荐使用系统提供的 logrotate 脚本/规则
- 不建议期望 SIGHUP 触发全面“重读配置”；FRR 的标准做法是使用 vtysh/frr-reload.py

---

## 协议层“无损/平滑”注意事项

- BGP
  - 优先使用 frr-reload.py；对需要邻居会话重置的变更，计划维护窗口
  - 可结合协议特性（graceful-restart、graceful-shutdown、邻居 soft-reconfig）降低影响
- IGP（OSPF/ISIS）
  - 大多数参数可热更，但区域/接口关键变更仍可能触发收敛
- VRF/接口/路由内核交互
  - 涉及 netns/VRF 结构变化，通常比纯协议参数更敏感

---

## 快速对照表

- 启动 FRR：systemctl start frr
- 停止 FRR：systemctl stop frr
- 重启 FRR：systemctl restart frr
- 热重载配置（推荐）：systemctl reload frr 或 frr-reload.py --reload /etc/frr/frr.conf
- 预检查变更：frr-reload.py --test /etc/frr/frr.conf
- 查看状态：systemctl status frr
- 保存当前运行配置：vtysh -c "write memory"
- 按配置文件批量下发：vtysh -b
- 启/停单个守护进程（若有单元）：systemctl restart|reload bgpd
- 启/停子进程（实验环境直启）：bgpd -d -f /etc/frr/bgpd.conf；停止用 pkill bgpd
- 启用/禁用某守护进程：编辑 /etc/frr/daemons 后 systemctl restart frr

---

如果你说明你的系统/发行版（如 Debian/Ubuntu/RHEL/Alpine、是否容器内）和你更倾向“全局控制”还是“单进程控制”，我可以给出更精确的一组命令与最佳实践清单。
