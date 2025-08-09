I'll search the repository to locate the implementation of "frr reload" (the frr-reload.py script and any service scripts that map a reload action to it) so I can give you accurate paths, options, and code references.

## frr reload 是什么

- 概念：frr reload 是一项“热重载”操作，用最小差异把磁盘上的配置（通常 /etc/frr/frr.conf）同步到正在运行的各 FRR 守护进程，尽量避免会话/邻居抖动和进程重启。
- 实现：核心由脚本 frr-reload.py 完成。它会：
  1) 通过 vtysh 读取当前运行配置（show running）
  2) 读取目标配置文件
  3) 计算差异
  4) 生成并下发所需的 vtysh 命令序列
- 要求：安装包含 frr-reload.py 的包（各发行版通常叫 frr-pythontools 或类似名字）。并启用 integrated vtysh config（见下文）。

---

## 代码位置与调用链（仓库内）

- frr-reload.py（执行核心）
  - 路径：tools/frr-reload.py
  - 读取/对比/下发配置的主要逻辑都在这里
  - 关键 CLI 参数（节选）：
````python path=tools/frr-reload.py mode=EXCERPT
parser.add_argument("--bindir", default="/usr/bin")
parser.add_argument("--confdir", default="/etc/frr")
parser.add_argument("--rundir", default="/var/run/frr")
parser.add_argument("--vty_socket", default=None)
parser.add_argument("--daemon", default="")
parser.add_argument("filename", help="Location of new frr config file")
````

- init 脚本如何映射 reload
  - systemd/OpenRC/SysV 脚本都会把 reload 映射到 frr-reload.py
  - OpenRC/SysV（通用 init 脚本模板）：
````sh path=tools/frrinit.sh.in mode=EXCERPT
reload)
  if [ ! -x "$RELOAD_SCRIPT" ]; then
    log_failure_msg "The frr-pythontools package is required for reload functionality."
    exit 1
  fi
  # …省略 watchdog 环境处理 …
  # 之后执行 $RELOAD_SCRIPT 做实际 reload
````
  - 另一份服务端脚本也同样调用：
````sh path=tools/frr.in mode=EXCERPT
reload)
  [ ! -x "$RELOAD_SCRIPT" ] && echo "Please install frr-pythontools package." && exit 0
  NEW_CONFIG_FILE="${2:-$C_PATH/frr.conf}"
  echo "Applying incremental changes"
  "$RELOAD_SCRIPT" --reload --bindir "$B_PATH" --confdir "$C_PATH" --rundir "$V_PATH" "$C_PATH/frr.conf"
  exit $?
  ;;
````

- 发行版暴露的“快捷入口”
  - 有的系统会安装一个小包装脚本 frr-reload（tools/frr-reload），直接 exec /usr/lib/frr/frr-reload.py --reload /etc/frr/frr.conf

---

## Alpine 上的使用方式

你有两种主流运行形态：OpenRC 管理服务，或容器内直接用 watchfrr。

1) 使用 OpenRC（推荐）
- 启停/状态（举例）
  - rc-service frr reload
  - rc-service frr restart
  - rc-service frr status
- reload 行为：OpenRC 的 /etc/init.d/frr 会在 reload 分支调用 frr-reload.py，对正在运行的守护进程做差异下发。
- 依赖：需要安装包含 /usr/lib/frr/frr-reload.py 的包（通常命名为 frr-pythontools）。
- 集成配置模式：
  - /etc/frr/vtysh.conf 中须启用 service integrated-vtysh-config（或至少不要显式写 no service integrated-vtysh-config）。否则 frr-reload 会拒绝执行（除非使用 --daemon 仅重载单个守护进程）。

2) 不用 OpenRC，仅用 watchfrr（常见于容器）
- 启动（示例）：watchfrr zebra bgpd ospfd
- 配置热更：
  - 直接调用 frr-reload.py，把 /etc/frr/frr.conf 的差异应用到运行态
    - 预检查：/usr/lib/frr/frr-reload.py --test /etc/frr/frr.conf
    - 执行：/usr/lib/frr/frr-reload.py --reload /etc/frr/frr.conf
  - 或更直接但更“暴力”的 vtysh -b（不做差异计算）
- 说明：watchfrr 仅负责拉起/保活进程；reload 不会重启进程，只通过 vtysh 向各守护进程注入配置变更。

提示：如果你偏好 Python 命令统一入口，可用 uv run /usr/lib/frr/frr-reload.py --reload /etc/frr/frr.conf；不过脚本有 shebang，直接执行即可。

---

## 构建/打包时如何使用（Alpine/容器实务）

- 安装组件
  - 必装：frr（守护进程、vtysh）
  - 建议：frr-pythontools（带 frr-reload.py；没有它就无法用 reload）
- 基础文件
  - /etc/frr/frr.conf：统一配置文件
  - /etc/frr/vtysh.conf：确保 integrated vtysh config 未被禁用（不要写 no service integrated-vtysh-config；或者显式添加 service integrated-vtysh-config）
- 运行形态选择
  - OpenRC：rc-update add frr default；构建镜像时保证 /etc/init.d/frr 存在；运行中直接 rc-service frr reload
  - 纯进程 + watchfrr：ENTRYPOINT/CMD 用 watchfrr 前台运行；在交付流水线或运维中用 frr-reload.py --test/--reload 进行热更
- 非默认路径/命名空间
  - frr-reload.py 支持 --bindir/--confdir/--rundir/--vty_socket/--daemon/--pathspace 等，用于定制 vtysh 路径、配置目录、运行目录、vty socket、仅对某守护进程/某 pathspace 执行等

---

## 常用命令小抄

- 预检查差异：/usr/lib/frr/frr-reload.py --test /etc/frr/frr.conf
- 热重载（最小差异）：/usr/lib/frr/frr-reload.py --reload /etc/frr/frr.conf
- OpenRC 方式：rc-service frr reload
- 批量直接下发（不做差异）：vtysh -b
- 保存运行配置到磁盘：vtysh -c "write memory"

如需，我可以根据你当前镜像/容器的具体布局，给出一份最小可行 Dockerfile/启动脚本与 reload 流程清单。
