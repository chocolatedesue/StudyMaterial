# 1. 安装工具依赖
sudo make tools.install

# 2. 生成代码（按顺序）
make go.gen.ebpf.vmlinux  # 生成vmlinux.h
make go.gen.ebpf          # 生成eBPF代码
make go.gen.grpc          # 生成gRPC代码（可选）

# 3. 管理Go模块
make go.init              # 初始化模块
make go.replace.netlink   # 替换依赖
make go.tidy             # 整理依赖

# 4. 构建项目
make build               # 构建所有组件

# 或者一键执行（推荐）
make go.gen              # 包含所有代码生成
make build               # 自动处理依赖并构建

---

cd itools
make build

---

