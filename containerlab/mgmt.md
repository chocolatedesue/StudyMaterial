让我搜索 containerlab 中关于默认路由和外部网络连接的实现：

现在让我搜索更多关于管理网络和外部连接的具体实现：

现在让我查看更多关于默认路由注入的具体实现：

基于对 containerlab 代码的深入分析，我来详细解释 containerlab 如何自动给容器注入默认路由和外部网络连接：

## Containerlab 管理网络和外部连接机制

### 1. 默认管理网络配置

#### A. 默认网络参数

````go path=core/config.go mode=EXCERPT
const (
    // 默认管理网络名称
    dockerNetName     = "clab"
    // 默认 IPv4 子网
    dockerNetIPv4Addr = "172.20.20.0/24"
    // 默认 IPv6 子网  
    dockerNetIPv6Addr = "3fff:172:20:20::/64"
)
````

#### B. 管理网络初始化

````go path=core/clab.go mode=EXCERPT
func (c *CLab) initMgmtNetwork() error {
    // 1. 设置默认网络名称
    if c.Config.Mgmt.Network == "" {
        c.Config.Mgmt.Network = dockerNetName  // "clab"
    }

    // 2. 设置默认子网
    if c.Config.Mgmt.IPv4Subnet == "" && c.Config.Mgmt.IPv6Subnet == "" {
        c.Config.Mgmt.IPv4Subnet = dockerNetIPv4Addr  // "172.20.20.0/24"
        c.Config.Mgmt.IPv6Subnet = dockerNetIPv6Addr  // "3fff:172:20:20::/64"
    }

    // 3. 默认启用外部访问
    if c.Config.Mgmt.ExternalAccess == nil {
        c.Config.Mgmt.ExternalAccess = new(bool)
        *c.Config.Mgmt.ExternalAccess = true  // 默认启用
    }

    return nil
}
````

### 2. Docker 网络创建和配置

#### A. 网络创建过程

````go path=runtime/docker/docker.go mode=EXCERPT
func (d *DockerRuntime) createMgmtBridge(nctx context.Context, bridgeName string) (string, error) {
    log.Info("Creating docker network",
        "name", d.mgmt.Network,           // "clab"
        "IPv4 subnet", d.mgmt.IPv4Subnet, // "172.20.20.0/24"
        "IPv6 subnet", d.mgmt.IPv6Subnet, // "3fff:172:20:20::/64"
        "MTU", d.mgmt.MTU)

    // 配置 IPAM (IP Address Management)
    ipam := &networkapi.IPAM{
        Driver: "default",
        Config: ipamConfig,  // 包含子网和网关配置
    }

    // 网络选项配置
    netwOpts := map[string]string{
        "com.docker.network.driver.mtu": strconv.Itoa(d.mgmt.MTU),
    }

    // Docker 28+ 启用 NAT unprotected 模式
    if semver.Compare(d.version, "v28.0.0") > 0 {
        netwOpts[bridgeGatewayModeIPv4Option] = natUnprotectedValue
        netwOpts[bridgeGatewayModeIPv6Option] = natUnprotectedValue
    }

    // 创建 Docker 网络
    opts := networkapi.CreateOptions{
        Driver:     "bridge",
        EnableIPv6: utils.Pointer(enableIPv6),
        IPAM:       ipam,
        Internal:   false,  // 允许外部访问
        Attachable: false,
        Options:    netwOpts,
    }

    netCreateResponse, err := d.Client.NetworkCreate(nctx, d.mgmt.Network, opts)
    return bridgeName, err
}
````

### 3. 容器网络配置

#### A. 容器连接到管理网络

````go path=runtime/docker/docker.go mode=EXCERPT
// 容器网络配置
containerNetworkingConfig.EndpointsConfig = map[string]*networkapi.EndpointSettings{
    d.mgmt.Network: {  // "clab" 网络
        IPAMConfig: &networkapi.EndpointIPAMConfig{
            IPv4Address: node.MgmtIPv4Address,  // 管理 IPv4 地址
            IPv6Address: node.MgmtIPv6Address,  // 管理 IPv6 地址
        },
        Aliases: node.Aliases,
    },
}
````

#### B. 网关信息获取和注入

````go path=nodes/default_node.go mode=EXCERPT
func (d *DefaultNode) UpdateConfigWithRuntimeInfo(ctx context.Context) error {
    // 获取容器的网络设置
    netSettings := cnts[0].NetworkSettings
    
    // 更新管理网络信息
    d.Cfg.MgmtIPv4Address = netSettings.IPv4addr
    d.Cfg.MgmtIPv4PrefixLength = netSettings.IPv4pLen
    d.Cfg.MgmtIPv6Address = netSettings.IPv6addr
    d.Cfg.MgmtIPv6PrefixLength = netSettings.IPv6pLen
    
    // 关键：获取网关信息
    d.Cfg.MgmtIPv4Gateway = netSettings.IPv4Gw  // Docker 网络的网关
    d.Cfg.MgmtIPv6Gateway = netSettings.IPv6Gw
    
    return nil
}
````

### 4. 设备配置中的默认路由注入

#### A. Cisco 设备（cEOS/XRd）

````go path=nodes/ceos/ceos.cfg mode=EXCERPT
// cEOS 配置模板
{{ if .MgmtIPv4Gateway }}ip route {{ if .Env.CLAB_MGMT_VRF }}vrf {{ .Env.CLAB_MGMT_VRF }} {{end}}0.0.0.0/0 {{ .MgmtIPv4Gateway }}{{end}}
{{ if .MgmtIPv6Gateway }}ipv6 route {{ if .Env.CLAB_MGMT_VRF }}vrf {{ .Env.CLAB_MGMT_VRF }} {{end}}::0/0 {{ .MgmtIPv6Gateway }}{{end}}
````

实际生成的配置：
```bash
# IPv4 默认路由
ip route 0.0.0.0/0 172.20.20.1

# IPv6 默认路由  
ipv6 route ::/0 3fff:172:20:20::1
```

#### B. Nokia SR Linux

````go path=nodes/srl/srl_default_config.go.tpl mode=EXCERPT
// SR Linux 配置模板会自动配置管理网络
set / system dns network-instance mgmt
set / system json-rpc-server admin-state enable network-instance mgmt
````

#### C. Cisco IOL

````go path=nodes/iol/iol.cfg.tmpl mode=EXCERPT
// IOL 配置模板
interface Ethernet0/0
 vrf forwarding clab-mgmt
 ip address {{ .MgmtIPv4Addr }} {{ .MgmtIPv4SubnetMask }}
 ipv6 address {{ .MgmtIPv6Addr }}/{{ .MgmtIPv6PrefixLen }}
!
// 默认路由配置
ip route vrf clab-mgmt 0.0.0.0 0.0.0.0 Ethernet0/0 {{ .MgmtIPv4GW }}
ipv6 route vrf clab-mgmt ::/0 Ethernet0/0 {{ .MgmtIPv6GW }}
````

### 5. 防火墙规则和外部访问

#### A. 自动防火墙规则配置

````go path=runtime/docker/firewall.go mode=EXCERPT
func (d *DockerRuntime) installMgmtNetworkFwdRule() (err error) {
    if !*d.mgmt.ExternalAccess {
        return nil  // 如果禁用外部访问，跳过
    }

    f, err := firewall.NewFirewallClient()
    if err != nil {
        return err
    }

    // 安装出站规则
    r := definitions.FirewallRule{
        Interface: d.mgmt.Bridge,           // clab 网桥
        Direction: definitions.OutDirection,
        Chain:     definitions.DockerUserChain,
        Table:     definitions.FilterTable,
        Action:    definitions.AcceptAction,
        Comment:   definitions.ContainerlabComment,
    }
    err = f.InstallForwardingRules(r)

    // 安装入站规则
    r.Direction = definitions.InDirection
    err = f.InstallForwardingRules(r)
    
    return err
}
````

#### B. 等价的 iptables 规则
```bash
# containerlab 自动添加的防火墙规则
iptables -I DOCKER-USER -o br-<network-id> -j ACCEPT
iptables -I DOCKER-USER -i br-<network-id> -j ACCEPT
```

### 6. DNS 配置

#### A. DNS 服务器自动提取

````go path=core/clab.go mode=EXCERPT
func (c *CLab) extractDNSServers(filesys fs.FS) error {
    // 从主机的 resolv.conf 提取 DNS 服务器
    DNSServers, err := utils.ExtractDNSServersFromResolvConf(filesys,
        []string{"etc/resolv.conf", "run/systemd/resolve/resolv.conf"})
    
    // 为所有节点设置 DNS 服务器
    for _, n := range c.Nodes {
        if n.Config().DNS.Servers == nil {
            n.Config().DNS.Servers = DNSServers
        }
    }
    
    return nil
}
````

### 7. 完整的网络连接流程

```
1. 创建管理网络 "clab" (172.20.20.0/24)
   ↓
2. 创建 Linux bridge (br-<network-id>)
   ↓
3. 配置网关 (172.20.20.1)
   ↓
4. 容器连接到管理网络
   ↓
5. 获取容器 IP 和网关信息
   ↓
6. 在容器内配置默认路由
   ↓
7. 安装防火墙规则允许外部访问
   ↓
8. 配置 DNS 服务器
```

### 8. 实际验证

你可以通过以下方式验证：

#### A. 查看管理网络
```bash
# 查看 containerlab 创建的网络
docker network ls | grep clab

# 查看网络详情
docker network inspect clab
```

#### B. 查看容器路由
```bash
# 进入容器查看路由表
docker exec -it clab-lab-node1 ip route show

# 输出示例：
# default via 172.20.20.1 dev eth0
# 172.20.20.0/24 dev eth0 proto kernel scope link src 172.20.20.10
```

#### C. 测试外部连接
```bash
# 在容器内测试外部连接
docker exec -it clab-lab-node1 ping 8.8.8.8
docker exec -it clab-lab-node1 curl -I https://google.com
```

### 9. 配置选项

#### A. 禁用外部访问
```yaml
mgmt:
  external-access: false  # 禁用外部访问
```

#### B. 自定义管理网络
```yaml
mgmt:
  network: custom-mgmt
  ipv4-subnet: 192.168.100.0/24
  ipv6-subnet: 2001:db8::/64
```

#### C. 使用现有网络
```yaml
mgmt:
  network: bridge  # 使用 Docker 默认网络
```

## 总结

Containerlab 确实会自动为所有容器注入默认路由和外部网络连接：

1. **自动创建管理网络**：默认 `clab` 网络 (172.20.20.0/24)
2. **自动配置网关**：Docker 网络的第一个 IP (172.20.20.1)
3. **自动注入默认路由**：在设备配置模板中添加默认路由
4. **自动配置防火墙**：允许容器访问外部网络
5. **自动配置 DNS**：从主机复制 DNS 设置

这个设计让容器能够：
- 相互通信（同一管理网络）
- 访问外部网络（默认路由 + 防火墙规则）
- 被外部访问（防火墙规则 + 端口映射）
- 解析域名（DNS 配置）

这就是为什么你在 containerlab 创建的容器中可以直接访问互联网的原因！
