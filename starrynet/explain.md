I'll scan the repository to identify the main modules, entry points, and how components interact so I can summarize the architecture and runtime flow.

I'll quickly list the starrynet package directory to see all modules so the architecture summary is complete.

I'll open the key modules to capture their responsibilities and how they interact: starrynet/cli.py, sn_observer.py, sn_orchestrater.py, log.py, clean.py, and __init__.py. This will let me describe the runtime flow precisely.

## 总览
StarryNet 是一个用于“卫星互联网星座”仿真的工具集。它通过远程机器的 Docker Swarm 容器群来模拟卫星和地面站节点，使用 tc netem 注入链路时延/丢包/带宽，结合 Skyfield/SGP4 计算星历与可见性，并用 Bird(OSPF) 做路由收敛。使用者可通过交互式 CLI 或脚本下达操作（创建节点、建链、启动路由、注入损伤、发起 ping/iperf、导出路由等），并按时间序列推进仿真与拓扑变化。

## 目录结构（主要部分）
- bin/sn
  - 项目命令行入口（安装后提供 sn 可执行脚本）。解析参数后实例化核心 StarryNet 类并进入交互式 CLI。
- starrynet/
  - cli.py：交互式命令行（starrynet>）命令集合，直接调用 StarryNet 实例的方法。
  - sn_synchronizer.py：核心 StarryNet 类（本地控制器）。负责：读取配置、连接远程、准备数据、对外暴露 create_nodes/create_links/run_routing_deamon/start_emulation 等操作。
  - sn_observer.py：观测/计算模块。计算轨道位置、卫星—卫星/卫星—地面可见性，生成每秒的链路延迟矩阵与位置数据，并按 OSPF 生成 Bird 配置。
  - sn_orchestrater.py：远程编排脚本（在远端机器上执行）。创建 Docker 网络（ISL/GSL）、连接容器接口、设定 tc netem，按文件更新链路时延，注入/恢复损伤，分发/启动 Bird。
  - sn_utils.py：工具与线程封装。含 Paramiko SSH/SFTP 初始化、远程命令执行、若干线程类（初始化目录/节点/链路/路由/仿真/停止）、业务函数（ping/perf/route 导出、损伤/恢复、时延更新等）。
  - log.py：日志封装（自定义 OUTPUT 级别，CLI 友好输出）。
  - clean.py：本地清理脚本（删除本机 Docker 服务和网络）。
- example.py
  - 使用 API 的示例脚本（直接调用 StarryNet 方法一次跑通流程）。
- config.json
  - 示例配置（星座参数、策略、远端机器凭据等）。
- tools/requirements.txt, install.sh, setup.py
  - 依赖安装与打包脚本。

## 核心模块职责与交互
- starrynet.sn_synchronizer.StarryNet（本地控制器）
  - 初始化：读取配置（sn_utils.sn_load_file）、建立远端 SSH/SFTP、初始化工作目录、计算 delay/position 数据（sn_observer.calculate_delay）、生成 Bird 配置（sn_observer.generate_conf）。
  - 对外方法（被 CLI/脚本调用）：
    - create_nodes：在远端创建 Docker 服务副本、重命名容器并记录容器列表。
    - create_links：将 orchestrater 脚本与初始延迟文件传至远端，构建 ISL/GSL 网络、连接容器接口并设置 netem（延迟/丢包/带宽）。
    - run_routing_deamon：把 Bird 配置分发到每个容器并启动 Bird。
    - start_emulation：启动仿真线程，按 Topo_leo_change.txt 推进时间片；周期性更新链路时延、注入/恢复损伤，发起 ping/iperf，导出路由与资源占用等。
    - stop_emulation：调用远端 orchestrater 停止仿真（删服务与网络）。
    - get_* / set_*：查询距离/邻居/位置/IP，设置损伤/恢复/下一跳/测量等，均由仿真线程在命中时间点执行。
- starrynet.sn_observer.Observer（离线数据与配置生成）
  - 使用 Skyfield/SGP4 计算每秒卫星 LLA 与笛卡尔坐标，结合地面站经纬度计算可视性与距离，换算链路延迟，输出：
    - position/t.txt、delay/t.txt
    - 将 delay 矩阵二值化序列对比生成 Topo_leo_change.txt（描述何时增删哪些链路及持续时间）
  - 生成 Bird OSPF 配置（每容器一个 B<ID>.conf），并通过 SFTP 放至远端对应目录。
- starrynet.sn_orchestrater（远端执行器）
  - 按不同命令行参数执行：
    - 初始化：依据 delay/1.txt 构建 ISL 与 GSL 的 Docker network、连接容器、重命名接口为 B<node>-eth<peer>，并用 tc netem 设置 delay/loss/rate。
    - 路由：将 Bird 配置复制进容器并启动 bird 进程；等待收敛。
    - 更新：按 delay/t.txt 批量变更 tc 延迟。
    - 损伤/恢复：批量调整 tc 丢包率或恢复。
    - 停止：移除 docker service、清理网络。
- starrynet.cli.CLI（交互式控制台）
  - 命令如：create_nodes、create_links、run_routing_deamon、get_distance、get_neighbors、get_GSes、get_position、get_IP、get_utility、set_damage、set_recovery、check_routing_table、set_next_hop、set_ping、set_perf、start_emulation、stop_emulation 等，直连 StarryNet 实例方法。

## 运行时数据与输出
- 本地工作目录（由配置路径派生）：<config_dir>/<cons_name>-<布局>-<高度>-<倾角>-<链路策略>-<选路策略>/
  - delay/t.txt、position/t.txt
  - Topo_leo_change.txt（描述拓扑变化的时间轴）
  - conf/bird-<sat_count>-<gs_count>/B<ID>.conf
  - 运行期产物：ping-*, perf-*, route-*, utility-info_*.txt
- 远端工作目录（home 下相同子路径）
  - 接收 orchestrater.py、delay/*.txt、Bird 配置等，作为远端操作依据。

## 典型运行流程（CLI）
1) 启动 CLI
- 安装后执行 sn（或直接 uv run bin/sn）
- sn 解析参数：-p 配置路径（虽然当前实现实际读取 ./config.json，见下方“注意事项”）、-i hello 间隔、-n 节点数（用于 AS 范围）、-g 地面站经纬度
- 实例化 StarryNet：连接远端、准备目录、计算 delay/position、生成并推送 Bird 配置
- 进入 starrynet> 提示符
2) 在 CLI 中依次执行
- create_nodes：在远端创建 N 个容器（Docker service replicas），重命名容器
- create_links：据 delay/1.txt 构建 ISL/GSL 网络并设置 netem
- run_routing_deamon：分发并启动 Bird，等待收敛
- 可选地安排事件：set_damage / set_recovery / set_next_hop / set_ping / set_perf / check_routing_table / get_utility
- start_emulation：按 Topo_leo_change.txt 推进，定时更新链路/执行测量/记录输出
- stop_emulation：清理
3) 运行期与结束
- 结果文件保存在本地配置目录下的生成子目录
- 退出 CLI 后，bin/sn 会调用 clean.py 做一次本地清理

## 如何本地运行
- 准备
  - 修改 config.json 中的远端机器 IP/用户名/密码
  - 确保远端主机已安装 Docker（建议启用 Swarm 模式）、能拉取镜像 lwsen/starlab_node:1.0，容器内具备 bird、iproute2、tc、iperf3 等工具
  - 安装依赖（可用 install.sh，或自己安装 tools/requirements.txt 中的包）
- 两种方式
  - 交互式 CLI：
    - uv run bin/sn
    - 在提示符依次执行：create_nodes → create_links → run_routing_deamon → start_emulation
  - 脚本方式：
    - uv run python example.py
    - 示例中构造 StarryNet 并调用同样的 API 顺序

注：命令执行建议用 uv run 来替代直接 python 运行（例如 uv run python example.py 或 uv run bin/sn）。

## 配置与依赖
- 配置文件：config.json（名称、轨道数、每轨卫星数、持续时长、更新周期、带宽/丢包、IP 版本、路由策略、地面站/天线、远端凭据等）
- 主要依赖
  - skyfield、sgp4：轨道与位置计算
  - numpy：矩阵运算
  - paramiko：远端 SSH/SFTP
  - requests：工具（当前未见对外接口调用）
  - 以及 bird（容器内）、docker 与 tc netem（远端主机/容器）

## 注意事项（潜在坑与不一致）
- 配置路径不一致：sn_utils.sn_load_file 固定从 ./config.json 读取，不使用 bin/sn 传入的 -p 路径；请确保运行目录下存在 config.json。README 也建议把 config.json、starrynet、example.py 放在同一工作目录。
- 远端清理/本地清理差异：stop_emulation 使用远端 orchestrater 清理；bin/sn 的退出路径也会执行本地 clean.py；严格区分本机与远端环境。
- 远端前置条件：需要 Docker Swarm、镜像、容器内工具齐备；tc netem 与 Bird 必须可用，否则建链/路由会失败。
- 时间推进：仿真以秒为单位推进，Topo_leo_change.txt 是链路增删的时间表；更新延迟按 update_interval 触发。

## 快速记忆卡
- 入口：bin/sn → StarryNet → CLI
- 计算与配置：Observer（位置/延迟/Bird 配置）
- 远端编排：sn_orchestrater（建网络、连容器、tc、Bird）
- 控制流：create_nodes → create_links → run_routing_deamon → start_emulation → stop_emulation
- 成果：delay/position/Topo、ping/perf/route/utility 输出文件

需要我画一张组件/时序图，或演示一段最小可跑的命令序列吗？
