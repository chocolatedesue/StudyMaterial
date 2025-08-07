这是一个非常重要的问题！让我查看FRR中如何处理路由重分发时的环路防护机制：

现在让我查看更多关于路由重分发环路防护的具体机制：

现在让我查看更多关于路由距离和环路防护的机制：

基于我对FRR代码的深入分析，现在我可以详细回答您关于路由重分发环路防护机制的问题：

## 路由重分发环路防护机制

FRR采用了多层防护机制来避免路由重分发环路：

### 1. **管理距离（Administrative Distance）防护**

````c path=lib/frrdistance.h mode=EXCERPT
/* Default Administrative Distance of each protocol. */
#define ZEBRA_KERNEL_DISTANCE_DEFAULT       0
#define ZEBRA_CONNECT_DISTANCE_DEFAULT      0
#define ZEBRA_STATIC_DISTANCE_DEFAULT       1
#define ZEBRA_RIP_DISTANCE_DEFAULT        120
#define ZEBRA_RIPNG_DISTANCE_DEFAULT      120
#define ZEBRA_OSPF_DISTANCE_DEFAULT       110
#define ZEBRA_OSPF6_DISTANCE_DEFAULT      110
#define ZEBRA_ISIS_DISTANCE_DEFAULT       115
#define ZEBRA_IBGP_DISTANCE_DEFAULT       200
#define ZEBRA_EBGP_DISTANCE_DEFAULT        20
````

**距离值越小优先级越高**：
- **eBGP**: 20
- **OSPF/OSPFv6**: 110  
- **iBGP**: 200

这确保了即使发生重分发环路，**原始BGP路由**总是优于**重分发回来的路由**。

### 2. **路由起源检查**

````c path=ospf6d/ospf6_zebra.c mode=EXCERPT
if (request->path.origin.adv_router == ospf6->router_id
    && (request->path.type == OSPF6_PATH_TYPE_EXTERNAL1
	|| request->path.type == OSPF6_PATH_TYPE_EXTERNAL2)) {
	if (IS_OSPF6_DEBUG_ZEBRA(SEND))
		zlog_debug("  Ignore self-originated external route");
	return;
}
````

**自起源路由过滤**：
- OSPF不会重新安装自己起源的外部路由
- 防止路由器接收到自己通告的路由

### 3. **路由标记（Route Tag）机制**

````c path=ospf6d/ospf6_asbr.c mode=EXCERPT
static route_tag_t ospf6_as_external_lsa_get_tag(struct ospf6_lsa *lsa)
{
	struct ospf6_as_external_lsa *external;
	
	if (!CHECK_FLAG(external->bits_metric, OSPF6_ASBR_BIT_T))
		return 0;
		
	// 提取路由标记
	memcpy(&network_order, (caddr_t)external + tag_offset,
	       sizeof(network_order));
	return ntohl(network_order);
}
````

**标记用途**：
- 标识路由来源协议
- 通过route-map过滤特定标记的路由
- 防止重分发环路

### 4. **BGP路由重分发时的隐式删除**

````c path=bgpd/bgp_zebra.c mode=EXCERPT
if (add) {
	/*
	 * The ADD message is actually an UPDATE and there is no
	 * explicit DEL for a prior redistributed route, if any. 
	 * So, perform an implicit DEL processing for the same 
	 * redistributed route from any other source type.
	 */
	for (i = 0; i < ZEBRA_ROUTE_MAX; i++) {
		if (i != api.type)
			bgp_redistribute_delete(bgp, &api.prefix, i,
						api.instance);
	}
}
````

**防重复机制**：
- 添加新的重分发路由时，自动删除来自其他协议的同前缀路由
- 确保每个前缀只有一个重分发来源

### 5. **实际环路防护示例**

#### 场景：BGP → OSPF → BGP 环路

```
[R1-BGP] ←→ [R2-BGP+OSPF] ←→ [R3-OSPF] ←→ [R4-OSPF+BGP] ←→ [R5-BGP]
```

**防护机制工作流程**：

1. **R2配置重分发**：
```bash
router ospf6
 redistribute bgp metric 100 metric-type 2 tag 65001
```

2. **R4接收OSPF外部路由**：
   - 路由标记：65001
   - 距离：110（OSPF外部）

3. **R4重分发回BGP时的防护**：
```bash
router bgp 65002
 redistribute ospf6 route-map OSPF-TO-BGP

route-map OSPF-TO-BGP deny 10
 match tag 65001    # 拒绝来自BGP的路由
route-map OSPF-TO-BGP permit 20
```

### 6. **距离值防护实例**

````c path=ospf6d/ospf6_top.c mode=EXCERPT
DEFUN (ospf6_distance_ospf6,
       ospf6_distance_ospf6_cmd,
       "distance ospf6 {intra-area (1-255)|inter-area (1-255)|external (1-255)}",
       "External routes\n"
       "Distance for external routes\n")
````

**配置示例**：
```bash
router ospf6
 distance ospf6 external 150  # 设置外部路由距离为150

router bgp 65001
 distance bgp 20 200 200      # eBGP=20, iBGP=200, local=200
```

**结果**：即使OSPF重分发BGP路由后再重分发回BGP，原始eBGP路由（距离20）仍优于重分发路由（距离150）。

### 7. **Route-map过滤机制**

````c path=ospf6d/ospf6_asbr.c mode=EXCERPT
static enum route_map_cmd_result_t
ospf6_routemap_rule_match_tag(void *rule, const struct prefix *p, void *object)
{
	route_tag_t *tag = rule;
	struct ospf6_route *route = object;
	struct ospf6_external_info *info = route->route_option;

	if (info->tag == *tag)
		return RMAP_MATCH;

	return RMAP_NOMATCH;
}
````

**高级防护配置**：
```bash
# 在重分发点设置标记
router ospf6
 redistribute bgp metric 100 route-map BGP-TO-OSPF

route-map BGP-TO-OSPF permit 10
 set tag 65001

# 在反向重分发点过滤
router bgp 65002
 redistribute ospf6 route-map OSPF-TO-BGP

route-map OSPF-TO-BGP deny 10
 match tag 65001
route-map OSPF-TO-BGP permit 20
```

### 8. **默认传递的信息**

重分发过程中**自动传递**的信息：
- **路由标记（Tag）**：标识路由来源
- **度量值（Metric）**：可配置或使用默认值
- **路由类型**：外部路由类型（Type-1/Type-2）
- **管理距离**：协议默认距离

**不会自动传递**：
- 原始协议的特定属性
- BGP的AS_PATH、Community等属性
- OSPF的区域信息

### 9. **最佳实践建议**

1. **使用路由标记**：
```bash
redistribute bgp tag 65001
```

2. **配置route-map过滤**：
```bash
route-map REDIST-FILTER deny 10
 match tag 65001
```

3. **调整管理距离**：
```bash
distance ospf6 external 150
```

4. **限制重分发范围**：
```bash
redistribute bgp route-map SELECTIVE-REDIST
```

通过这些多层防护机制，FRR有效防止了路由重分发环路，确保网络的稳定性和路由的正确性。
