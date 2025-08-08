让我查看OSPFv3的默认宣告行为，并与ISIS进行对比。

现在让我查看OSPFv3接口配置和路由宣告的具体实现：

现在让我查看OSPFv3和ISIS在P2P连接上的具体行为差异：

基于我对FRR中OSPFv3和ISIS代码的深入分析，我可以详细回答你的问题：

## OSPFv3 vs ISIS 默认宣告行为对比

### 1. **基本宣告行为相似性**

**OSPFv3和ISIS在默认宣告方面基本一致：**

- **接口IP地址**：都会宣告启用协议的接口上配置的IP地址
- **Loopback地址**：都会宣告loopback接口的IP地址（通常设为passive）
- **默认路由**：都需要显式配置才会宣告

### 2. **配置命令对比**

**OSPFv3配置：**
```` path=tests/topotests/ospf6_gr_topo1/rt3/ospf6d.conf mode=EXCERPT
interface lo
 ipv6 ospf area 0
 ipv6 ospf network point-to-point

interface eth-rt2
 ipv6 ospf network point-to-point
 ipv6 ospf area 0
````

**ISIS配置：**
```` path=tests/topotests/isis_tilfa_topo1/rt1/isisd.conf mode=EXCERPT
interface lo
 ip router isis 1
 ipv6 router isis 1
 isis passive

interface eth-sw1
 ip router isis 1
 ipv6 router isis 1
````

### 3. **P2P连接上的行为差异**

**OSPFv3在P2P连接上的特殊处理：**

````c path=ospf6d/ospf6_interface.c mode=EXCERPT
if (oi->type == OSPF_IFTYPE_LOOPBACK ||
    oi->type == OSPF_IFTYPE_POINTOMULTIPOINT ||
    oi->type == OSPF_IFTYPE_POINTOPOINT) {
    struct ospf6_route *la_route;

    la_route = ospf6_route_create(oi->area->ospf6);
    la_route->prefix = *c->address;
    la_route->prefix.prefixlen = 128;
    la_route->prefix_options |= OSPF6_PREFIX_OPTION_LA;
````

**OSPFv3会额外宣告：**
- **Link-Local地址**：在P2P、P2MP和loopback接口上会宣告/128的link-local地址
- **连接前缀的特殊处理**：可以通过`p2p-p2mp connected-prefixes include/exclude`控制

### 4. **LSA生成差异**

**OSPFv3的LSA结构更复杂：**

````c path=ospf6d/ospf6_intra.c mode=EXCERPT
/* connected prefix to advertise */
for (route = ospf6_route_head(oi->route_connected); route;
     route = ospf6_route_next(route)) {
    op->prefix_length = route->prefix.prefixlen;
    op->prefix_options = route->prefix_options;
    op->prefix_metric = htons(0);
    memcpy(OSPF6_PREFIX_BODY(op), &route->prefix.u.prefix6,
           OSPF6_PREFIX_SPACE(op->prefix_length));
    op = OSPF6_PREFIX_NEXT(op);
}
````

**OSPFv3需要生成多种LSA：**
- **Link LSA**：包含接口的link-local地址和连接前缀
- **Intra-Area-Prefix LSA**：包含区域内前缀信息
- **Router LSA**：包含路由器邻接关系

**ISIS相对简单：**
- 直接在LSP中包含IP可达性TLV
- 不需要分离的LSA类型

### 5. **Passive接口行为差异**

**ISIS的advertise-passive-only功能：**

````c path=isisd/isis_cli.c mode=EXCERPT
DEFPY_YANG(advertise_passive_only, advertise_passive_only_cmd,
           "[no] advertise-passive-only",
           NO_STR "Advertise prefixes of passive interfaces only\n")
````

**ISIS提供更灵活的passive接口控制：**
- 可以配置只宣告passive接口的前缀
- OSPFv3没有类似的全局控制选项

### 6. **P2P连接流程对比**

**在P2P连接上，流程基本一致：**

1. **邻居发现**：都通过Hello报文
2. **邻接建立**：都有类似的状态机
3. **LSA/LSP交换**：都进行链路状态信息交换
4. **路由计算**：都使用SPF算法

**但OSPFv3在P2P上有额外步骤：**
- 需要生成Link LSA
- 需要在Intra-Area-Prefix LSA中包含连接前缀
- 有更复杂的LSA依赖关系

## 总结

**OSPFv3相比ISIS会多宣告：**

1. **Link-Local地址**：在P2P、P2MP、loopback接口上宣告/128地址
2. **更详细的前缀选项**：包含prefix options字段
3. **接口特定的LSA**：Link LSA包含接口级别的信息

**在P2P连接上：**
- **基本流程一致**：邻居发现→邻接建立→信息交换→路由计算
- **OSPFv3更复杂**：需要生成更多类型的LSA，有更复杂的依赖关系
- **ISIS更简洁**：直接在LSP中包含所有信息

**配置复杂度：**
- **ISIS**：`ip router isis` + `isis passive`
- **OSPFv3**：`ipv6 ospf area` + `ipv6 ospf passive` + 可能需要网络类型配置

总的来说，OSPFv3在功能上更丰富但也更复杂，ISIS相对简洁但功能完整。在P2P环境下，两者的核心宣告行为相似，但OSPFv3会提供更多的细节信息。
