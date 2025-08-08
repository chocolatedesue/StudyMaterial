我来帮你重新梳理special topo的核心需求和任务。首先让我查看当前的代码结构和相关文件，了解现有的实现情况。

现在让我查看相关的模型定义，特别是SpecialTopologyConfig：

## 背景与目标
- 基于 6x6 网格的 “Special” 拓扑，用于模拟企业多域网络
- 结合 OSPFv3（域内）与 BGP（域间），纯 IPv6 环境，可选 BFD
- 只实例化“有连接”的节点与接口，ContainerLab 仅落地必要物理链路

## 核心需求（What）
- 拓扑类型
  - 新增 TopologyType.SPECIAL，支持 base_topology=GRID/TORUS
  - include_base_connections: 是否叠加基础拓扑（Grid/Torus）邻居
- 节点角色
  - Source 节点：(1,4)
  - Destination 节点：(4,1)
  - Gateway 节点：从 internal_bridge_edges + torus_bridge_edges 的端点集合推导（约16个）
  - 其余为 Internal 节点；仅保留有连接的节点
- 连接类型与落地策略
  - 内部桥接 internal_bridge_edges：物理链路；在 ContainerLab 中创建
  - Torus 桥接 torus_bridge_edges：逻辑连接；仅体现在路由配置，不在 ContainerLab 中创建
  - 基础拓扑邻居：按 include_base_connections 决定是否加入（Grid/Torus）
  - 接口按实际连接自动分配；未用方向的接口不生成
- 配置生成
  - OSPFv3：全网启用；支持 hello/dead/spf 定时配置；优先级可调
  - BGP：仅 Gateway 节点启用；支持 IPv6 与 OSPFv3/Connected 重分发；邻居按“接口对接口”生成
- 地址与标识
  - Router ID：10.x.x.x 规则（按坐标/规模）
  - Loopback IPv6：2001:db8:1000:area:row:col::1/128
  - 链路 IPv6：/127 点对点，2001:db8:2000:… 前缀，基于全局唯一 link_id 生成
- CLI 与目录
  - 命令：python setup/generate_ospfv3_functional.py special [参数]
  - 生成目录：ospfv3_special6x6_test/，包含 clab.yaml 与各路由器 {daemons, zebra, ospf6d, staticd, bgpd}.conf

## 关键设计与约束（How）
- 邻居计算
  - get_special_neighbors(special_config, size)：基础邻居 + 内部桥接 + Torus 桥接（仅逻辑，用于路由/度量）
- 链路生成
  - generate_all_links(config)：仅对“基础邻居（若启用）+ 内部桥接”产出 ContainerLab 物理链路
  - Torus 桥接不生成物理 link，但在协议配置与访邻统计中体现
- 节点类型判定
  - get_node_type：在 SPECIAL 模式下优先识别 Source/Dest/Gateway；否则 Internal
- 目前规模限制：Special 仅支持 6x6

## 交付物
- ContainerLab 拓扑文件：仅包含 internal_bridge_edges（+ 可选基础邻居）的物理 links
- 每路由器配置文件：OSPFv3 全部节点；BGP 仅 Gateway 节点
- 生成脚本与使用示例、用例脚本、说明文档

## 验收标准（Definition of Done）
- ContainerLab 拓扑仅含应有的物理链路（不含 Torus 桥接）
- Gateway 节点准确，且仅 Gateway 生成 bgpd.conf 并启用进程
- 源/目的节点正确；所有活跃节点与接口与连接数与设计一致
- IPv6 地址与 /127 链路地址唯一且匹配两端
- CLI 参数生效（基础拓扑选择、是否叠加基础连接、OSPF 定时、BGP AS、BFD）
- 验证脚本或用例运行通过（配置文件结构与内容检查、连接/邻居/角色检查）

## 任务拆解与里程碑
1) 模型与规则
- 定义/确认 SpecialTopologyConfig 字段：source_node, dest_node, gateway_nodes, internal_bridge_edges, torus_bridge_edges, base_topology, include_base_connections
- 节点类型与邻居计算逻辑（get_special_neighbors、get_node_type）

2) 链路与接口
- generate_all_links：基础邻居（可选）+ 内部桥接 物理链路；Torus 桥接不落地
- 接口映射与禁用未用方向接口

3) 协议配置
- OSPFv3：定时/优先级、区域（Special 默认单区域）
- BGP：仅 Gateway，AS 号、IPv6、重分发、基于接口的邻居与激活

4) CLI 与输出
- special 子命令参数：base_topology、include_base、bgp-as、hello/dead/spf、enable-bfd
- 生成目录结构与 clab.yaml

5) 验证与文档
- 测试/验证脚本：节点与连接计数、角色、BGP/OSPF配置、ContainerLab link 校验
- 使用指南与用例脚本更新

## 风险与注意事项
- 接口命名与方向一致性（ethN 对齐左右上下）
- 地址唯一性与可达性；/127 对端地址分配正确
- 当 include_base_connections=true 时的链路去重与统计
- BGP 仅在 Gateway 启用，防止误启用

## 后续扩展（Nice to have）
- 支持非 6x6 的 Special 模式与可配置的桥接边
- 更灵活的域/区域切分、策略化 BGP 邻接
- 自动化端到端验证与可视化

如果你希望，我可以把上面“任务拆解”转成可跟踪的任务清单并按优先级排期，或根据你当前进度标注完成度。
