# FRR BGP 添加新SAFI完整指南

## 概述

如果你只需要在BGP更新机制中添加一个新的SAFI并实现自定义逻辑，需要关注以下核心部分。本指南基于FRR代码分析，提供最小化修改路径。

## 1. 核心定义文件

### 1.1 SAFI枚举定义
**文件**: `lib/zebra.h`
```c
// 在SAFI枚举中添加新的SAFI
typedef enum {
    SAFI_UNSPEC = 0,
    SAFI_UNICAST = 1,
    SAFI_MULTICAST = 2,
    SAFI_MPLS_VPN = 3,
    SAFI_ENCAP = 4,
    SAFI_EVPN = 5,
    SAFI_LABELED_UNICAST = 6,
    SAFI_FLOWSPEC = 7,
    SAFI_BGP_LINK_STATE = 8,
    SAFI_YOUR_NEW_SAFI = 9,    // 添加你的新SAFI
    SAFI_MAX = 10              // 更新SAFI_MAX
} safi_t;
```

### 1.2 BGP地址族索引
**文件**: `bgpd/bgpd.h`
```c
// 在BGP_AF枚举中添加对应的索引
enum bgp_af_index {
    BGP_AF_START,
    BGP_AF_IPV4_UNICAST = BGP_AF_START,
    // ... 其他现有SAFI
    BGP_AF_IPV4_YOUR_NEW_SAFI,    // 为IPv4添加
    BGP_AF_IPV6_YOUR_NEW_SAFI,    // 为IPv6添加
    BGP_AF_MAX
};

// 在afindex函数中添加映射
static inline int afindex(afi_t afi, safi_t safi)
{
    switch (afi) {
    case AFI_IP:
        switch (safi) {
        // ... 现有case
        case SAFI_YOUR_NEW_SAFI:
            return BGP_AF_IPV4_YOUR_NEW_SAFI;
        }
        break;
    case AFI_IP6:
        switch (safi) {
        // ... 现有case  
        case SAFI_YOUR_NEW_SAFI:
            return BGP_AF_IPV6_YOUR_NEW_SAFI;
        }
        break;
    }
}
```

## 2. IANA标准映射

### 2.1 IANA SAFI定义
**文件**: `lib/iana_afi.h`
```c
// 添加IANA标准SAFI值
typedef enum {
    // ... 现有定义
    IANA_SAFI_YOUR_NEW_SAFI = XXX,  // 使用IANA分配的值
} iana_safi_t;

// 在转换函数中添加映射
static inline safi_t safi_iana2int(iana_safi_t safi)
{
    switch (safi) {
    // ... 现有case
    case IANA_SAFI_YOUR_NEW_SAFI:
        return SAFI_YOUR_NEW_SAFI;
    }
}

static inline iana_safi_t safi_int2iana(safi_t safi)
{
    switch (safi) {
    // ... 现有case
    case SAFI_YOUR_NEW_SAFI:
        return IANA_SAFI_YOUR_NEW_SAFI;
    }
}
```

## 3. 数据包处理

### 3.1 前缀编码/解码
**文件**: `bgpd/bgp_attr.c`

#### 前缀编码函数
```c
void bgp_packet_mpattr_prefix(struct stream *s, afi_t afi, safi_t safi,
                              const struct prefix *p, const struct prefix_rd *prd,
                              mpls_label_t *label, uint8_t num_labels,
                              bool addpath_capable, uint32_t addpath_tx_id,
                              struct attr *attr)
{
    switch (safi) {
    // ... 现有case
    case SAFI_YOUR_NEW_SAFI:
        // 实现你的前缀编码逻辑
        if (addpath_capable)
            stream_putl(s, addpath_tx_id);
        // 添加你的自定义前缀格式
        // stream_putc(s, your_prefix_length);
        // stream_put(s, your_custom_data, your_data_length);
        break;
    }
}
```

#### 前缀大小计算
```c
size_t bgp_packet_mpattr_prefix_size(afi_t afi, safi_t safi, const struct prefix *p)
{
    int size = PSIZE(p->prefixlen);
    
    switch (safi) {
    // ... 现有case
    case SAFI_YOUR_NEW_SAFI:
        // 计算你的自定义前缀大小
        size += your_custom_prefix_overhead;
        break;
    }
    
    return size;
}
```

## 4. 路由处理逻辑

### 4.1 路由表结构处理
**文件**: `bgpd/bgp_route.c`

#### 节点获取逻辑
```c
struct bgp_dest *bgp_afi_node_get(struct bgp_table *table, afi_t afi, safi_t safi,
                                  const struct prefix *p, struct prefix_rd *prd)
{
    // 如果你的SAFI需要特殊的表结构（如VPN类型的两级表）
    if ((safi == SAFI_MPLS_VPN) || (safi == SAFI_ENCAP) || 
        (safi == SAFI_EVPN) || (safi == SAFI_YOUR_NEW_SAFI)) {
        // 实现两级表逻辑
        pdest = bgp_node_get(table, (struct prefix *)prd);
        // ... 两级表处理
    }
    
    // 否则使用标准单级表
    dest = bgp_node_get(table, p);
    return dest;
}
```

### 4.2 路由更新处理
```c
// 在bgp_update函数中添加特殊处理
void bgp_update(struct peer *peer, const struct prefix *p, ...)
{
    // ... 标准处理逻辑
    
    // 添加你的SAFI特殊处理
    if (safi == SAFI_YOUR_NEW_SAFI) {
        // 实现你的自定义路由处理逻辑
        your_custom_route_processing(bgp, pi, p, attr);
    }
    
    // ... 继续标准处理
}
```

## 5. 更新组机制集成

### 5.1 子组通告处理
**文件**: `bgpd/bgp_updgrp_adv.c`
```c
void subgroup_announce_table(struct update_subgroup *subgrp, struct bgp_table *table)
{
    // ... 现有逻辑
    
    // 如果你的SAFI不需要默认路由通告
    if (safi != SAFI_MPLS_VPN && safi != SAFI_ENCAP && safi != SAFI_EVPN &&
        safi != SAFI_YOUR_NEW_SAFI &&  // 添加你的SAFI
        CHECK_FLAG(peer->af_flags[afi][safi], PEER_FLAG_DEFAULT_ORIGINATE))
        subgroup_default_originate(subgrp, false);
}
```

### 5.2 路由通告检查
```c
void subgroup_announce_route(struct update_subgroup *subgrp)
{
    // 如果你的SAFI需要特殊的通告逻辑
    if (SUBGRP_SAFI(subgrp) != SAFI_MPLS_VPN &&
        SUBGRP_SAFI(subgrp) != SAFI_ENCAP &&
        SUBGRP_SAFI(subgrp) != SAFI_EVPN &&
        SUBGRP_SAFI(subgrp) != SAFI_BGP_LINK_STATE &&
        SUBGRP_SAFI(subgrp) != SAFI_YOUR_NEW_SAFI) {  // 添加你的SAFI
        // 标准单级表处理
    } else {
        // 特殊处理逻辑
    }
}
```

## 6. 激活和配置

### 6.1 SAFI激活逻辑
**文件**: `bgpd/bgpd.c`
```c
int peer_activate_af(struct peer *peer, afi_t afi, safi_t safi)
{
    // ... 现有逻辑
    
    // 如果你的SAFI需要特殊的激活处理
    if (safi == SAFI_YOUR_NEW_SAFI) {
        // 实现特殊的激活逻辑
        your_safi_activation_logic(peer, afi, safi);
    }
    
    return ret;
}
```

## 7. 最小化实现步骤

### 步骤1: 基础定义
1. 在`lib/zebra.h`中添加SAFI枚举
2. 在`bgpd/bgpd.h`中添加BGP_AF索引和afindex映射
3. 在`lib/iana_afi.h`中添加IANA映射

### 步骤2: 数据包处理
1. 在`bgpd/bgp_attr.c`中实现前缀编码/解码
2. 实现前缀大小计算

### 步骤3: 路由处理
1. 在`bgpd/bgp_route.c`中添加路由处理逻辑
2. 根据需要实现特殊的表结构处理

### 步骤4: 更新组集成
1. 在`bgpd/bgp_updgrp_adv.c`中添加通告逻辑
2. 确保更新组机制正确处理新SAFI

### 步骤5: 测试验证
1. 编译验证
2. 功能测试
3. 与现有SAFI的兼容性测试

## 8. 注意事项

1. **向后兼容性**: 确保新SAFI不影响现有功能
2. **内存管理**: 注意新增数据结构的内存分配和释放
3. **错误处理**: 添加适当的错误检查和处理
4. **调试支持**: 添加调试日志和统计信息
5. **文档更新**: 更新相关文档和帮助信息

## 9. 详细实现示例

### 9.1 完整的SAFI添加示例

假设我们要添加一个名为`SAFI_CUSTOM_PROTOCOL`的新SAFI：

#### 步骤1: 基础定义修改

**lib/zebra.h**
```c
typedef enum {
    SAFI_UNSPEC = 0,
    SAFI_UNICAST = 1,
    SAFI_MULTICAST = 2,
    SAFI_MPLS_VPN = 3,
    SAFI_ENCAP = 4,
    SAFI_EVPN = 5,
    SAFI_LABELED_UNICAST = 6,
    SAFI_FLOWSPEC = 7,
    SAFI_BGP_LINK_STATE = 8,
    SAFI_CUSTOM_PROTOCOL = 9,    // 新增
    SAFI_MAX = 10                // 更新
} safi_t;
```

**bgpd/bgpd.h**
```c
enum bgp_af_index {
    BGP_AF_START,
    BGP_AF_IPV4_UNICAST = BGP_AF_START,
    BGP_AF_IPV4_MULTICAST,
    BGP_AF_IPV4_VPN,
    BGP_AF_IPV6_UNICAST,
    BGP_AF_IPV6_MULTICAST,
    BGP_AF_IPV6_VPN,
    BGP_AF_IPV4_ENCAP,
    BGP_AF_IPV6_ENCAP,
    BGP_AF_L2VPN_EVPN,
    BGP_AF_IPV4_LBL_UNICAST,
    BGP_AF_IPV6_LBL_UNICAST,
    BGP_AF_IPV4_FLOWSPEC,
    BGP_AF_IPV6_FLOWSPEC,
    BGP_AF_IPV4_CUSTOM_PROTOCOL,  // 新增
    BGP_AF_IPV6_CUSTOM_PROTOCOL,  // 新增
    BGP_AF_MAX
};

// afindex函数修改
static inline int afindex(afi_t afi, safi_t safi)
{
    switch (afi) {
    case AFI_IP:
        switch (safi) {
        case SAFI_UNICAST:
            return BGP_AF_IPV4_UNICAST;
        // ... 其他现有case
        case SAFI_CUSTOM_PROTOCOL:
            return BGP_AF_IPV4_CUSTOM_PROTOCOL;
        }
        break;
    case AFI_IP6:
        switch (safi) {
        case SAFI_UNICAST:
            return BGP_AF_IPV6_UNICAST;
        // ... 其他现有case
        case SAFI_CUSTOM_PROTOCOL:
            return BGP_AF_IPV6_CUSTOM_PROTOCOL;
        }
        break;
    }
    return BGP_AF_MAX;
}
```

#### 步骤2: 数据包处理实现

**bgpd/bgp_attr.c**
```c
void bgp_packet_mpattr_prefix(struct stream *s, afi_t afi, safi_t safi,
                              const struct prefix *p, const struct prefix_rd *prd,
                              mpls_label_t *label, uint8_t num_labels,
                              bool addpath_capable, uint32_t addpath_tx_id,
                              struct attr *attr)
{
    switch (safi) {
    // ... 现有case
    case SAFI_CUSTOM_PROTOCOL:
        if (addpath_capable)
            stream_putl(s, addpath_tx_id);

        // 自定义协议前缀格式
        // 例如: 长度 + 前缀 + 自定义数据
        stream_putc(s, p->prefixlen + 32);  // 前缀长度 + 自定义数据长度
        stream_put(s, &p->u.prefix, PSIZE(p->prefixlen));

        // 添加自定义协议特定数据
        if (attr && attr->custom_data) {
            stream_put(s, attr->custom_data, 32);
        } else {
            // 填充默认数据
            uint8_t default_data[32] = {0};
            stream_put(s, default_data, 32);
        }
        break;
    }
}

size_t bgp_packet_mpattr_prefix_size(afi_t afi, safi_t safi, const struct prefix *p)
{
    int size = PSIZE(p->prefixlen);

    switch (safi) {
    // ... 现有case
    case SAFI_CUSTOM_PROTOCOL:
        size += 32;  // 自定义数据大小
        break;
    }

    return size;
}
```

#### 步骤3: 路由处理逻辑

**bgpd/bgp_route.c**
```c
// 在bgp_update函数中添加自定义处理
void bgp_update(struct peer *peer, const struct prefix *p, uint32_t addpath_id,
                struct attr *attr, afi_t afi, safi_t safi, int type,
                int sub_type, struct prefix_rd *prd, mpls_label_t *label,
                uint8_t num_labels, int soft_reconfig, struct bgp_route_evpn *evpn)
{
    // ... 标准处理逻辑

    // 自定义SAFI特殊处理
    if (safi == SAFI_CUSTOM_PROTOCOL) {
        // 验证自定义协议数据
        if (!validate_custom_protocol_data(attr)) {
            reason = "Invalid custom protocol data";
            goto filtered;
        }

        // 处理自定义协议特定逻辑
        process_custom_protocol_route(bgp, p, attr, afi, safi);
    }

    // ... 继续标准处理
    bgp_process(bgp, dest, new, afi, safi);

    // 自定义SAFI的后处理
    if (safi == SAFI_CUSTOM_PROTOCOL) {
        custom_protocol_post_process(bgp, new, p, attr);
    }
}

// 自定义协议验证函数
static bool validate_custom_protocol_data(struct attr *attr)
{
    if (!attr || !attr->custom_data)
        return false;

    // 实现你的验证逻辑
    return true;
}

// 自定义协议路由处理
static void process_custom_protocol_route(struct bgp *bgp, const struct prefix *p,
                                         struct attr *attr, afi_t afi, safi_t safi)
{
    // 实现自定义协议的路由处理逻辑
    // 例如: 特殊的路由计算、标记、转换等
}
```

### 9.2 更新组机制集成

**bgpd/bgp_updgrp_adv.c**
```c
void subgroup_announce_table(struct update_subgroup *subgrp, struct bgp_table *table)
{
    // ... 现有逻辑

    // 自定义SAFI不需要默认路由通告
    if (safi != SAFI_MPLS_VPN && safi != SAFI_ENCAP && safi != SAFI_EVPN &&
        safi != SAFI_CUSTOM_PROTOCOL &&  // 添加自定义SAFI
        CHECK_FLAG(peer->af_flags[afi][safi], PEER_FLAG_DEFAULT_ORIGINATE))
        subgroup_default_originate(subgrp, false);

    // ... 继续处理
}

bool subgroup_announce_check(struct bgp_dest *dest, struct bgp_path_info *pi,
                            struct update_subgroup *subgrp, const struct prefix *p,
                            struct attr *attr, struct attr *post_attr)
{
    // ... 现有逻辑

    // 自定义SAFI的通告检查
    if (safi == SAFI_CUSTOM_PROTOCOL) {
        // 实现自定义的通告检查逻辑
        if (!custom_protocol_announce_check(pi, peer, attr)) {
            return false;
        }
    }

    // ... 继续标准检查
}
```

### 9.3 CLI配置支持

如果需要CLI配置支持，需要修改：

**bgpd/bgp_vty.c**
```c
// 添加address-family配置命令
DEFUN(address_family_ipv4_custom,
      address_family_ipv4_custom_cmd,
      "address-family ipv4 custom-protocol",
      "Enter Address Family command mode\n"
      "Address Family\n"
      "Custom Protocol SAFI\n")
{
    vty->node = BGP_IPV4_CUSTOM_NODE;
    return CMD_SUCCESS;
}

// 添加neighbor激活命令
DEFUN(neighbor_activate_custom,
      neighbor_activate_custom_cmd,
      "neighbor <A.B.C.D|X:X::X:X|WORD> activate",
      NEIGHBOR_STR
      NEIGHBOR_ADDR_STR2
      "Enable the Address Family for this Neighbor\n")
{
    return peer_activate_af_vty(vty, argv[0]->arg, AFI_IP, SAFI_CUSTOM_PROTOCOL);
}
```

### 9.4 调试和监控支持

**bgpd/bgp_debug.c**
```c
// 添加调试支持
DEFUN(debug_bgp_custom_protocol,
      debug_bgp_custom_protocol_cmd,
      "debug bgp custom-protocol",
      DEBUG_STR
      BGP_STR
      "BGP custom protocol\n")
{
    if (vty->node == CONFIG_NODE)
        DEBUG_ON(custom_protocol, CUSTOM_PROTOCOL);
    else
        TERM_DEBUG_ON(custom_protocol, CUSTOM_PROTOCOL);

    return CMD_SUCCESS;
}
```

## 10. 编译和测试

### 10.1 编译验证
```bash
# 清理并重新编译
make clean
./configure --enable-dev-build
make -j$(nproc)
```

### 10.2 基本功能测试
```bash
# 启动BGP daemon
sudo ./bgpd -f /etc/frr/bgpd.conf

# 进入vtysh测试配置
vtysh
configure terminal
router bgp 65001
address-family ipv4 custom-protocol
neighbor 192.168.1.2 activate
```

### 10.3 调试验证
```bash
# 启用调试
debug bgp neighbor-events
debug bgp updates
debug bgp custom-protocol

# 查看状态
show bgp ipv4 custom-protocol summary
show bgp ipv4 custom-protocol neighbors
```
