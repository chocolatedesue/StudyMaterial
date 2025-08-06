好的，我们来详细梳理一下论文实验结果部分的图表，并用严谨的学术语言描述它们所测量的指标。

---

### 实验结果图表解读

#### Figure 13: 小规模测试床功能验证 (Small-Scale Testbed Functionality Validation)

*   **测量指标:** 该图集用于定性验证LBP协议原型的**功能完备性、路由可达性与数据平面转发性能**。
*   **图表解读:**
    *   **(a) Testbed Setup:** 展示了由6个服务器节点构成的物理拓扑结构，作为实验环境的示意。
    *   **(b) LBP's routing table in R2:** 展示了节点R2的IPv6路由表。关键在于**`L>*`**条目，它表示LBP协议成功计算并安装了一条指向`2001:da8:26d:1066:1b3a::/80`网段的路由。这证明了LBP控制平面的**路由计算与安装功能**是正常的。
    *   **(c) Packets received by the receiver:** 这是一个时间序列图，X轴为时间（秒），Y轴为数据包的源/目的地址。图中连续不断的记录流表明，在动态拓扑下，接收端能够持续、无中断地接收到发送端发来的数据包，验证了LBP路由的**端到端连通性与鲁棒性**。
    *   **(d) Throughput in 1Gbps links:** X轴为时间（秒），Y轴为吞吐量（Mbps）。曲线显示吞吐量接近并饱和于1Gbps的链路容量，证明LBP的数据平面转发引擎（基于Linux内核）是高效的，没有成为性能瓶颈。
*   **核心结论:** Figure 13从协议实现和系统层面证明了LBP方案在技术上是**可行且高效**的。

#### Figure 15: 网络带宽提升效果 (Improvement on Network Bandwidth)

*   **测量指标:** **平均用户带宽 (Average User Bandwidth, $BW_{avg}$)**，单位为Mbps。
*   **图表解读:**
    *   **X轴:** 不同的LEO卫星星座（Starlink, Kuiper, Telesat）。
    *   **Y轴:** 平均每个用户能够获得的带宽。
    *   **对比对象:** `Legacy`（传统地面站锚点方案）、`Optimal`（理论最优方案）、`LBP`（本文提出的方案）。
*   **核心结论:** LBP的带宽（红色柱）远高于Legacy（蓝色柱），且非常接近Optimal（绿色柱）。这定量地证明了LBP通过移除地面站瓶颈，能够**显著提升网络总容量和用户平均可用带宽**。

#### Figure 16: 网络传播延迟改善分布 (Improvement on Network Propagation Latency)

*   **测量指标:** **网络传播延迟**的**累积分布函数 (Cumulative Distribution Function, CDF)**。延迟通过**跳数(hop count)**和**毫秒(delay(ms))**两个维度来衡量。
*   **图表解读:**
    *   **X轴:** 延迟的具体数值（跳数或毫秒）。
    *   **Y轴:** 累积概率（0到1.00）。CDF曲线的含义是“有多大比例的连接，其延迟小于或等于X轴的对应值”。
    *   **对比对象:** `Legacy`, `Optimal`, `LBP`三条曲线。
*   **核心结论:** LBP的CDF曲线整体位于Legacy曲线的左侧，表明对于绝大多数用户连接，LBP都提供了比Legacy方案低得多的延迟。同时，LBP曲线紧密贴合Optimal曲线，证明其路径选择接近理论最优。此图从**统计分布**上证实了LBP在**降低网络延迟**上的普适性和高效性。

#### Figure 17: 传播延迟动态变化展示 (A showcase of improvement on propagation latency)

*   **测量指标:** **特定用户对**的端到端延迟随时间变化的**时间序列**。
*   **图表解读:**
    *   **X轴:** 仿真时间（分钟）。
    *   **Y轴:** 端到端延迟（跳数或毫秒）。
    *   **对比对象:** `Optimal`, `Legacy`, `LBP`三条随时间变化的曲线。
*   **核心结论:** Legacy方案的延迟曲线（蓝色）表现出非常高且不稳定的特性，这源于其三角路由。LBP的延迟曲线（红色）则低得多，并且与Optimal曲线（绿色）的轨迹高度重合且平稳。此图展示了LBP在**单个连接的动态过程中**也能持续提供低延迟和高稳定性的服务。

#### Figure 18: 传播延迟抖动改善情况 (LBP's propagation latency jitter)

*   **测量指标:** **延迟抖动 (Latency Jitter)**，这里通过计算延迟的**方差 (variance)**来量化，包括**var(hop count)**和**var(delay)**。
*   **图表解读:**
    *   这是一个CDF图，**X轴**为延迟方差的具体数值，**Y轴**为累积概率。
    *   **对比对象:** `orbit direction-aware`（LBP采用的感知轨道方向的切换策略）与`orbit direction-oblivious`（一种不考虑轨道方向的朴素切换策略，例如总是切换到仰角最高的卫星）。
*   **核心结论:** LBP策略的CDF曲线（红色）远在朴素策略（蓝色）的左侧，这意味着采用LBP的切换策略，绝大多数连接的延迟方差都非常小。这证明了LBP的**轨道感知切换策略能有效抑制延迟抖动，提升网络服务质量的稳定性**。

#### Figure 19: 网络可用性与可达性改善 (Improvement on network availability & reachability)

*   **测量指标:**
    *   **(a) 网络可用性 (Network Availability, $A_{net}$ %):** 定义为网络处于路由收敛、可提供服务状态的时间占总时间的百分比。
    *   **(b) 路由可达性 (Routing Reachability, $R_{net}$ %):** 定义为在所有随机生成的源-目的对中，能够成功找到路由的比例。
*   **图表解读:**
    *   **(a) Network availability:** 对比了LBP与传统的分布式路由协议（如OSPF）。
    *   **(b) Routing reachability:** 对比了完整的LBP协议与一个简化的、不感知轨道方向的地理路由（`Orbit direction-oblivious GR`）。
*   **核心结论:**
    *   (a) LBP因其本地化路由特性，可用性接近**100%**；而OSPF因需要频繁的全局路由收敛，在LEO高动态环境下可用性极低（<10%）。
    *   (b) 完整的LBP协议实现了**100%**的可达性；而简化的地理路由存在路由黑洞（局部最小值问题），可达性受损。这证明了LBP中的**轨道方向感知是保证路由可达性的关键创新**。