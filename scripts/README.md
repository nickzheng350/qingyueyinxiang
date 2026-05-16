#!/bin/bash
# 脚本使用说明生成器

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cat << 'EOF'
========================================
  自动化脚本使用说明
========================================

📋 可用脚本列表

1. run_grpc_test.sh
   用途：自动运行 gRPC 跨语言调用测试
   位置：scripts/run_grpc_test.sh
   
   功能：
   ✓ 检查 Python 和 Rust 依赖
   ✓ 编译 Protobuf 文件
   ✓ 启动 Python gRPC 服务端
   ✓ 运行 Rust gRPC 客户端
   ✓ 显示测试结果和日志
   
   使用方法：
   chmod +x scripts/run_grpc_test.sh
   ./scripts/run_grpc_test.sh
   
   输出：
   - 服务端日志：/tmp/grpc_python_server.log
   - 服务端 PID: /tmp/grpc_server.pid

2. build_wasm.sh
   用途：构建 Rust 技能引擎为 WASM 并集成到 Vue 项目
   位置：scripts/build_wasm.sh
   
   功能：
   ✓ 检查 Rust 和 wasm-pack 依赖
   ✓ 构建 WASM 模块
   ✓ 复制文件到 Vue 项目
   ✓ 更新 Vite 配置
   ✓ 创建使用示例文档
   ✓ 更新 package.json
   
   使用方法：
   chmod +x scripts/build_wasm.sh
   ./scripts/build_wasm.sh
   
   输出目录：
   ui/src/wasm/
   ├── skill_engine_bg.wasm
   ├── skill_engine.js
   ├── skill_engine.d.ts
   └── index.js

========================================
  集成到构建流程
========================================

在 package.json 中添加：

{
  "scripts": {
    "build:wasm": "../scripts/build_wasm.sh",
    "build:all": "npm run build:wasm && npm run build",
    "test:grpc": "../scripts/run_grpc_test.sh"
  }
}

使用方式：
npm run build:wasm      # 构建 WASM
npm run build:all       # 构建 WASM + Vue 项目
npm run test:grpc       # 运行 gRPC 测试

========================================
  故障排查
========================================

问题 1: wasm-pack 未找到
解决：curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh

问题 2: Python gRPC 依赖缺失
解决：pip3 install grpcio grpcio-tools --user

问题 3: Rust 编译失败
解决：cargo clean && cargo update

问题 4: WASM 加载失败
解决：检查浏览器控制台，确保服务器配置了正确的 MIME 类型

========================================
  性能优化建议
========================================

1. WASM 预加载
   在 main.ts 中初始化：
   import { initWasm } from '@/wasm'
   await initWasm()

2. 增量构建
   只构建变更的模块：
   wasm-pack build --target web --dev

3. 并行构建
   使用 GNU parallel 并行构建多个 WASM 模块

4. 缓存优化
   在 CI/CD 中缓存 ~/.cargo 和 pkg 目录

========================================
  下一步
========================================

1. 运行 gRPC 测试验证跨语言调用：
   ./scripts/run_grpc_test.sh

2. 构建 WASM 模块：
   ./scripts/build_wasm.sh

3. 在 Vue 组件中使用：
   import { initWasm, install_skill } from '@/wasm'
   await initWasm()
   const result = await install_skill('skill_id', 'path.tar.gz')

4. 查看 Axum 示例代码：
   docs/axum_file_server.rs

EOF
