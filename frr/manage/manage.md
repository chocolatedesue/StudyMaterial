## 官方推荐的启动/停止方式

首选使用系统服务管理器（systemd）。大多数发行版的 FRR 包都会安装 frr.service，它由 watchfrr 统一拉起各守护进程。

- 启动 FRR
  - systemctl start frr
- 停止 FRR
  - systemctl stop frr
- 重启 FRR
  - systemctl restart frr
- 开机自启动
  - systemctl enable frr
- 查看状态/日志
  - systemctl status frr
  - journalctl -u frr -e

说明：
- 具体哪些守护进程会被启动由 /etc/frr/daemons 控制（zebra 必须启用，其他按需如 bgpd、ospfd、staticd 等）。
- 配置推荐集中在 /etc/frr/frr.conf；服务启动后通常会通过 vtysh -b 一次性应用该配置。


## 非 systemd/容器场景的官方方式

- 使用 watchfrr 直接管理进程（官方自带）
  - 启动（示例）：watchfrr -d zebra bgpd staticd
  - 停止：pkill watchfrr（watchfrr 退出会停止它托管的守护进程）
- 传统 SysV（较老系统）
  - service frr start|stop|restart 或 /etc/init.d/frr start|stop

说明：
- watchfrr 负责按顺序启动、拉起后续守护进程并监控它们；等所有进程就绪后，再统一用 vtysh -b 应用 /etc/frr/frr.conf。
- 在容器中使用 watchfrr 时，通常需要增加相应 Linux capability（至少 NET_ADMIN；如果还要加载内核模块则需更高权限）。


## 在你仓库的 Docker 镜像里的默认行为

- 以 ubuntu-ci 为例：容器启动时执行 docker/ubuntu-ci/docker-start，这个脚本只做两件事：
  - 在 Ubuntu 内核上尝试 sudo modprobe mpls-router mpls-iptunnel vrf
  - 无限 sleep 以保持容器存活
- 因此：容器默认不会自动启动 FRR，你需要进入容器后手动运行 watchfrr 或 systemctl（如果容器里运行了 systemd）来启动 FRR。

相关文件：
- Dockerfile：docker/ubuntu-ci/Dockerfile（通过 CMD 调用 docker-start）
- 启动脚本：docker/ubuntu-ci/docker-start

如果你使用的是 centos-8 的镜像，也有对应 docker/centos-8/docker-start，可按相同思路查看；通常这些 docker-start 都不会直接启动 FRR 守护进程，而是留给你手动启动。


## 常见操作提醒

- 启/停具体守护进程
  - 官方建议通过编辑 /etc/frr/daemons 决定启用哪些守护进程，然后整体 systemctl restart frr。
  - 单独测试时可直接运行二进制（如 /usr/lib/frr/bgpd -d …），但生产/常规建议用 watchfrr/systemd 统一托管。
- 应用/更新配置
  - 集中配置：vtysh -b 会应用 /etc/frr/frr.conf
  - 不中断更新：frr-reload.py 可对运行中配置做差异下发（各发行包一般带有该工具）
- 验证是否运行
  - pid 文件：/var/run/frr/*.pid
  - vtysh 查看：show ip route / show bgp summary 等业务命令
  - systemd 状态：systemctl status frr

如果你告诉我当前环境（发行版/是否容器/是否有 systemd），我可以给出一套最简可用的启动/停止命令脚本和注意项。
