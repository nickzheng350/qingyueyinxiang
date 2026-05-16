#!/bin/bash
# gRPC 跨语言调用验证脚本
# 自动启动 Python 服务端和 Rust 客户端

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  gRPC 跨语言调用验证"
echo "=========================================="
echo ""

# 检查依赖
check_dependencies() {
    echo "1. 检查依赖..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ 错误：未找到 python3"
        exit 1
    fi
    
    if ! command -v cargo &> /dev/null; then
        echo "❌ 错误：未找到 cargo"
        exit 1
    fi
    
    # 检查 Python gRPC 模块
    if ! python3 -c "import grpc" 2>/dev/null; then
        echo "❌ 错误：未找到 grpc 模块"
        echo "   请安装：python3 -m pip install grpcio"
        exit 1
    fi
    
    echo "   ✅ 依赖检查通过"
}

# 编译 Protobuf
compile_protobuf() {
    echo ""
    echo "2. 编译 Protobuf..."
    
    cd "$PROJECT_ROOT/grpc-python"
    
    python3 -m grpc_tools.protoc \
        --proto_path=../grpc-proto \
        --python_out=. \
        --grpc_python_out=. \
        ../grpc-proto/skill.proto
    
    echo "   ✅ Protobuf 编译完成"
}

# 启动 Python 服务端
start_python_server() {
    echo ""
    echo "3. 启动 Python gRPC 服务端..."
    
    cd "$PROJECT_ROOT/grpc-python"
    
    # 后台运行服务端
    python3 server.py > /tmp/grpc_python_server.log 2>&1 &
    SERVER_PID=$!
    
    echo "   服务端 PID: $SERVER_PID"
    echo "   日志文件：/tmp/grpc_python_server.log"
    
    # 等待服务端启动
    echo "   等待服务端启动..."
    sleep 2
    
    # 检查服务端是否启动成功
    if ps -p $SERVER_PID > /dev/null; then
        echo "   ✅ 服务端启动成功"
    else
        echo "   ❌ 服务端启动失败，查看日志：/tmp/grpc_python_server.log"
        exit 1
    fi
    
    echo $SERVER_PID > /tmp/grpc_server.pid
}

# 编译并运行 Rust 客户端
run_rust_client() {
    echo ""
    echo "4. 编译并运行 Rust gRPC 客户端..."
    
    cd "$PROJECT_ROOT/grpc-rust"
    
    # 构建项目
    cargo build --release 2>&1 | tail -5
    
    # 运行客户端
    echo ""
    echo "   运行测试..."
    cargo run --release
    
    echo ""
    echo "   ✅ 客户端测试完成"
}

# 清理资源
cleanup() {
    echo ""
    echo "5. 清理资源..."
    
    if [ -f /tmp/grpc_server.pid ]; then
        SERVER_PID=$(cat /tmp/grpc_server.pid)
        if ps -p $SERVER_PID > /dev/null; then
            echo "   停止服务端 (PID: $SERVER_PID)..."
            kill $SERVER_PID 2>/dev/null || true
            rm /tmp/grpc_server.pid
        fi
    fi
    
    echo "   ✅ 清理完成"
}

# 显示服务端日志
show_server_logs() {
    echo ""
    echo "=== 服务端日志 (最后 20 行) ==="
    if [ -f /tmp/grpc_python_server.log ]; then
        tail -20 /tmp/grpc_python_server.log
    else
        echo "日志文件不存在"
    fi
}

# 主函数
main() {
    trap cleanup EXIT
    
    check_dependencies
    compile_protobuf
    start_python_server
    run_rust_client
    show_server_logs
    
    echo ""
    echo "=========================================="
    echo "  ✅ 验证完成！"
    echo "=========================================="
}

main "$@"
