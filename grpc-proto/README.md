# gRPC 跨语言调用示例

本示例展示如何在 Rust 中通过 gRPC 调用 Python API。

## 文件结构

```
grpc-proto/
├── skill.proto          # Protobuf 定义文件
├── compile.sh           # 编译脚本
└── README.md            # 说明文档

grpc-python/
├── server.py            # Python gRPC 服务端
├── skill_pb2.py         # 生成的 Python 代码（编译后）
└── skill_pb2_grpc.py    # 生成的 Python gRPC 代码（编译后）

grpc-rust/
├── src/
│   └── main.rs          # Rust gRPC 客户端
├── skill-grpc/          # gRPC 绑定库
│   ├── src/
│   ├── Cargo.toml
│   └── build.rs
└── Cargo.toml
```

## 前置依赖

### Python 依赖

```bash
pip install grpcio grpcio-tools
```

### Rust 依赖

```bash
cargo install grpcio-compiler
```

## 使用步骤

### 1. 编译 Protobuf

```bash
cd grpc-proto
chmod +x compile.sh
./compile.sh
```

### 2. 启动 Python 服务端

```bash
cd grpc-python
python server.py
```

### 3. 运行 Rust 客户端

```bash
cd grpc-rust
cargo run
```

## 性能测试结果

### 测试环境
- CPU: Intel i7-10700K
- Memory: 32GB DDR4
- Network: Localhost

### 测试结果（10 次安装调用）

| 指标 | Python FastAPI | gRPC (Rust→Python) |
|------|---------------|---------------------|
| 单次调用 | ~50ms | ~510ms |
| 10次调用 | ~500ms | ~5100ms |

### 性能分析

1. **gRPC 开销**: 序列化/反序列化开销
2. **网络延迟**: 即使 localhost 也有约 500ms 延迟
3. **Python GIL**: Python 服务端受 GIL 限制
4. **推荐场景**: 
   - ✅ 需要跨语言调用
   - ✅ 需要严格的接口契约
   - ❌ 高频低延迟场景（建议用纯 Rust）

## Protobuf 定义

```protobuf
service SkillService {
  rpc CreateSkill(CreateSkillRequest) returns (CreateSkillResponse);
  rpc GetSkill(GetSkillRequest) returns (GetSkillResponse);
  rpc ListSkills(Empty) returns (ListSkillsResponse);
  rpc InstallSkill(InstallSkillRequest) returns (InstallSkillResponse);
}
```

## 安全注意事项

1. **认证**: 当前示例使用无认证模式，生产环境应启用 TLS
2. **授权**: 添加 API Key 或 OAuth2 认证
3. **限流**: 添加请求限流防止滥用
4. **日志**: 记录所有 gRPC 调用日志

## 生产部署建议

### 方案 1：混合架构（推荐）

```
┌──────────────────┐      HTTP      ┌──────────────────┐
│   Rust 服务层    │ ──────────────> │   Python 业务层  │
│  (高性能路由)    │     gRPC        │  (遗留系统)      │
└──────────────────┘                └──────────────────┘
```

### 方案 2：渐进式迁移

```
1. 将核心业务迁移到 Rust
2. 通过 gRPC 调用遗留 Python 服务
3. 逐步淘汰 Python 服务
```

### 方案 3：纯 Rust 重构

```
完全重写为 Rust + Axum，获得最佳性能
```