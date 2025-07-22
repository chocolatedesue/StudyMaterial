我来详细梳理 FRR 中现有的 SRv6 策略和对应的代码实现：

# FRR SRv6 现有策略和代码梳理

## 1. SRv6 策略架构概览

### 1.1 代码模块分布
```
zebra/          - SRv6 定位器管理和内核接口
├── zebra_srv6.c
├── zebra_srv6_vty.c
└── zebra_srv6.h

pathd/          - SR-TE 策略管理
├── pathd.c
├── path_cli.c
├── path_zebra.c
└── pathd.h

bgpd/           - BGP SRv6 VPN 策略
├── bgp_srv6.c
├── bgp_srv6.h
└── bgp_vpn.c

isisd/          - ISIS SRv6 策略
├── isis_srv6.c
├── isis_srv6.h
└── isis_spf.c

lib/            - SRv6 基础定义
├── srv6.h
└── srv6.c
```

## 2. Zebra 层 SRv6 策略

### 2.1 定位器管理策略

````c path=zebra/zebra_srv6_vty.c mode=EXCERPT
/* 定位器配置命令 */
DEFUN_NOSH (srv6_locator,
            srv6_locator_cmd,
            "locator WORD",
            "Segment Routing SRv6 locator\n"
            "Specify locator-name\n")

/* 定位器前缀配置 */
DEFPY (locator_prefix,
       locator_prefix_cmd,
       "prefix X:X::X:X/M$prefix [block-len (16-64)$block_bit_len]  \
        [node-len (16-64)$node_bit_len] [func-bits (0-64)$func_bit_len]",
       "Configure SRv6 locator prefix\n")

/* uSID 行为配置 */
DEFPY (locator_behavior,
       locator_behavior_cmd,
       "[no] behavior usid",
       NO_STR
       "Configure SRv6 behavior\n"
       "Specify SRv6 behavior uSID\n")
````

### 2.2 现有定位器策略类型

#### 标准定位器策略
```c
struct srv6_locator {
    char name[SRV6_LOCNAME_SIZE];           // 定位器名称
    struct prefix_ipv6 prefix;              // IPv6 前缀
    uint8_t block_bits_length;              // 块长度 (默认40位)
    uint8_t node_bits_length;               // 节点长度 (默认24位)  
    uint8_t function_bits_length;           // 功能长度 (默认16位)
    uint8_t argument_bits_length;           // 参数长度 (默认0位)
    uint8_t flags;                          // 标志位
#define SRV6_LOCATOR_USID (1 << 0)         // uSID 标志
};
```

#### 配置策略示例
```frr
# 标准定位器
segment-routing
 srv6
  locators
   locator main
    prefix 2001:db8:1:1::/64 block-len 40 node-len 24 func-bits 16
   !
   
   # uSID定位器  
   locator usid-loc
    prefix 2001:db8:2::/48 func-bits 16
    behavior usid
   !
  !
 !
```

### 2.3 封装策略

````c path=zebra/zebra_srv6_vty.c mode=EXCERPT
/* 封装源地址配置 */
DEFPY (srv6_src_addr,
       srv6_src_addr_cmd,
       "source-address X:X::X:X$encap_src_addr",
       "Segment Routing SRv6 source address\n"
       "Specify source address for SRv6 encapsulation\n")
````

#### 封装策略配置
```frr
segment-routing
 srv6
  encapsulation
   source-address 2001:db8:1::1
  !
 !
```

## 3. PathD 层 SR-TE 策略

### 3.1 SR-TE 策略框架

````c path=pathd/pathd.h mode=EXCERPT
struct srte_policy {
    uint32_t color;                         // 策略颜色
    struct ipaddr endpoint;                 // 端点地址
    char name[64];                          // 策略名称
    mpls_label_t binding_sid;               // 绑定SID
    enum srte_protocol_origin protocol_origin; // 协议来源
    enum srte_policy_status status;         // 操作状态
    struct srte_candidate *best_candidate;  // 最佳候选路径
    struct srte_candidate_head candidate_paths; // 候选路径列表
};
````

### 3.2 现有 SR-TE 策略类型

#### 显式路径策略
````c path=pathd/path_cli.c mode=EXCERPT
/* SR-TE 策略配置 */
DEFPY_NOSH(
    srte_policy,
    srte_policy_cmd,
    "policy color (0-4294967295)$num endpoint <A.B.C.D|X:X::X:X>$endpoint",
    "Segment Routing Policy\n"
    "SR Policy color\n"
    "SR Policy endpoint\n")

/* 候选路径配置 */
DEFPY_NOSH(
    srte_candidate_path,
    srte_candidate_path_cmd,
    "candidate-path preference (0-4294967295)$preference name WORD$name explicit segment-list WORD$segment_list",
    "Candidate path\n"
    "Preference\n"
    "Explicit path\n"
    "Segment list\n")
````

#### SR-TE 策略配置示例
```frr
segment-routing
 traffic-eng
  # 低延迟策略
  policy color 100 endpoint 2001:db8:2::1
   name "Low-Latency-Path"
   binding-sid 1000
   candidate-path preference 200 name "primary" explicit segment-list sl-primary
   candidate-path preference 100 name "backup" explicit segment-list sl-backup
  !
  
  # 段列表定义
  segment-list sl-primary
   index 10 sid 2001:db8:1:1::100
   index 20 sid 2001:db8:2:1::100
  !
  
  segment-list sl-backup
   index 10 sid 2001:db8:3:1::100
   index 20 sid 2001:db8:2:1::100
  !
 !
```

### 3.3 策略状态管理

````c path=pathd/pathd.c mode=EXCERPT
/* 策略状态枚举 */
enum srte_policy_status {
    SRTE_POLICY_STATUS_DOWN = 0,
    SRTE_POLICY_STATUS_UP,
    SRTE_POLICY_STATUS_GOING_DOWN,
    SRTE_POLICY_STATUS_GOING_UP,
};

/* 策略更新函数 */
void srte_policy_update_binding_sid(struct srte_policy *policy, 
                                   mpls_label_t binding_sid)
{
    policy->binding_sid = binding_sid;
    SET_FLAG(policy->flags, F_POLICY_MODIFIED);
}
````

## 4. BGP SRv6 VPN 策略

### 4.1 BGP SRv6 策略结构

````frr path=tests/topotests/bgp_srv6l3vpn_sid/r1/bgpd.conf mode=EXCERPT
router bgp 1
 segment-routing srv6
  locator loc1
 !
 address-family ipv4 vpn
  neighbor 2001::2 activate
 exit-address-family
!

router bgp 1 vrf vrf10
 address-family ipv4 unicast
  sid vpn export auto                    # 自动SID导出
  rd vpn export 1:10                     # 路由区分符
  rt vpn both 99:99                      # 路由目标
  import vpn                             # VPN路由导入
  export vpn                             # VPN路由导出
 exit-address-family
!
````

### 4.2 SID 分配策略

#### 自动 SID 分配
```c
/* BGP SRv6 SID 分配策略 */
enum bgp_srv6_sid_alloc_mode {
    BGP_SRV6_SID_ALLOC_AUTO,              // 自动分配
    BGP_SRV6_SID_ALLOC_EXPLICIT,          // 显式指定
    BGP_SRV6_SID_ALLOC_POOL               // 从池中分配
};
```

#### SID 导出策略配置
```frr
router bgp 65001 vrf customer-a
 address-family ipv4 unicast
  # 自动SID分配
  sid vpn export auto
  
  # 显式SID指定
  sid vpn export 2001:db8:1:1::100
  
  # 从特定定位器分配
  sid vpn export auto locator backup-loc
 exit-address-family
```

### 4.3 路由策略集成

#### RT/RD 策略
```frr
router bgp 65001 vrf customer-a
 address-family ipv4 unicast
  # 路由区分符策略
  rd vpn export 65001:100
  rd vpn import 65001:100
  
  # 路由目标策略  
  rt vpn export 65001:100
  rt vpn import 65001:100
  rt vpn both 65001:200              # 同时导入导出
 exit-address-family
```

## 5. ISIS SRv6 策略

### 5.1 ISIS SRv6 集成

````c path=isisd/isis_srv6.c mode=EXCERPT
/* ISIS SRv6 配置结构 */
struct isis_srv6_db {
    struct {
        bool enabled;                       // SRv6 启用状态
        char srv6_locator_name[SRV6_LOCNAME_SIZE]; // 定位器名称
        uint8_t max_seg_left_msd;          // 最大段剩余深度
        uint8_t max_end_pop_msd;           // 最大端点弹出深度
        uint8_t max_h_encaps_msd;          // 最大H封装深度
        uint8_t max_end_d_msd;             // 最大端点D深度
        char srv6_ifname[IF_NAMESIZE];     // SRv6接口名称
    } config;
    
    struct list *srv6_locator_chunks;      // 定位器块列表
    struct list *srv6_sids;                // SID列表
    struct list *srv6_endx_sids;           // End.X SID列表
};
````

### 5.2 SID 分配策略

#### End SID 分配
```c
/* End SID 分配函数 */
struct isis_srv6_sid *
isis_srv6_sid_alloc(struct isis_area *area, 
                   struct srv6_locator_chunk *chunk,
                   enum srv6_endpoint_behavior_codepoint behavior,
                   int sid_func)
{
    struct isis_srv6_sid *sid;
    
    sid = XCALLOC(MTYPE_ISIS_SRV6_SID, sizeof(*sid));
    sid->sid = srv6_locator_request_sid(area, chunk, sid_func);
    sid->behavior = behavior;
    sid->locator = chunk;
    
    return sid;
}
```

#### End.X SID 分配策略
```c
/* End.X SID 行为类型 */
enum srv6_endx_behavior {
    SRV6_ENDPOINT_BEHAVIOR_END_X,          // 标准 End.X
    SRV6_ENDPOINT_BEHAVIOR_END_X_NEXT_CSID // uSID End.X
};
```

### 5.3 ISIS SRv6 配置示例

```frr
router isis CORE
 net 49.0001.0000.0000.0001.00
 is-type level-2-only
 
 # SRv6配置
 segment-routing srv6
  locator main
  max-seg-left-msd 10
  max-end-pop-msd 10
  max-h-encaps-msd 10
  max-end-d-msd 10
 !
 
 address-family ipv6 unicast
  multi-topology
 exit-address-family
!
```

## 6. 现有策略的限制和扩展点

### 6.1 当前策略限制

#### 路径计算限制
- **单一度量**：主要基于 IGP 度量
- **静态权重**：缺乏动态权重调整
- **约束支持**：有限的约束条件支持
- **算法固定**：主要使用标准 SPF

#### SID 管理限制
- **分配策略**：相对简单的分配机制
- **生命周期**：缺乏复杂的生命周期管理
- **冲突处理**：基础的冲突检测和处理
- **性能优化**：有限的性能优化策略

### 6.2 可扩展的策略点

#### 1. 定位器策略扩展
```c
/* 扩展定位器配置 */
struct srv6_locator_policy {
    enum srv6_alloc_strategy strategy;     // 分配策略
    struct srv6_constraints constraints;   // 约束条件
    struct srv6_optimization_params opts;  // 优化参数
    struct srv6_monitoring_config monitor; // 监控配置
};
```

#### 2. 路径计算策略扩展
```c
/* 自定义路径计算策略 */
struct srv6_path_policy {
    enum srv6_path_algorithm algorithm;    // 路径算法
    struct srv6_path_constraints constraints; // 路径约束
    struct srv6_optimization_objectives objectives; // 优化目标
    struct srv6_fallback_strategy fallback; // 回退策略
};
```

#### 3. 动态策略管理
```c
/* 动态策略管理 */
struct srv6_dynamic_policy {
    struct srv6_trigger_conditions triggers; // 触发条件
    struct srv6_adaptation_rules rules;      // 适应规则
    struct srv6_monitoring_metrics metrics;  // 监控指标
    struct srv6_action_handlers handlers;    // 动作处理器
};
```

## 7. 策略配置模板

### 7.1 基础策略模板
```frr
# 最小SRv6策略配置
segment-routing
 srv6
  locators
   locator main
    prefix 2001:db8:1:1::/64
   !
  !
 !
```

### 7.2 高级策略模板
```frr
# 完整SRv6策略配置
segment-routing
 srv6
  encapsulation
   source-address 2001:db8:1::1
  !
  locators
   locator primary
    prefix 2001:db8:1:1::/64 block-len 40 node-len 24 func-bits 16
    behavior usid
   !
   locator backup
    prefix 2001:db8:1:2::/64 func-bits 8
   !
  !
 !
 
 traffic-eng
  policy color 100 endpoint 2001:db8:2::1
   candidate-path preference 200 name "primary" explicit segment-list sl1
  !
  segment-list sl1
   index 10 sid 2001:db8:1:1::100
  !
 !
```

### 7.3 BGP SRv6 VPN 策略模板
```frr
router bgp 65001
 segment-routing srv6
  locator primary
 !
!

router bgp 65001 vrf customer
 address-family ipv4 unicast
  sid vpn export auto
  rd vpn export 65001:100
  rt vpn both 65001:100
  import vpn
  export vpn
 exit-address-family
!
```

## 8. 监控和调试策略

### 8.1 状态查看命令
```bash
# 查看SRv6策略状态
show segment-routing srv6 locator
show segment-routing srv6 sid

# 查看SR-TE策略
show segment-routing traffic-eng policy
show segment-routing traffic-eng segment-list

# 查看BGP SRv6状态
show bgp segment-routing srv6
show bgp ipv4 vpn summary
```

### 8.2 调试命令
```bash
# 启用调试
debug segment-routing srv6
debug bgp vpn
debug isis srv6

# 查看详细信息
show segment-routing srv6 locator detail
show segment-routing traffic-eng policy detail
```

这个梳理涵盖了 FRR 中现有的所有 SRv6 策略实现，包括定位器管理、SR-TE 策略、BGP VPN 策略和 ISIS 集成策略，为进一步的自定义扩展提供了清晰的基础。