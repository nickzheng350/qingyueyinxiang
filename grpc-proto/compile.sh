#!/bin/bash
# gRPC 编译脚本

echo "=== Compiling gRPC Protobuf ==="

# 编译 Python 代码
echo "1. Compiling Python bindings..."
cd ../grpc-python
python -m grpc_tools.protoc \
    --proto_path=../grpc-proto \
    --python_out=. \
    --grpc_python_out=. \
    ../grpc-proto/skill.proto

# 编译 Rust 代码
echo "2. Compiling Rust bindings..."
cd ../grpc-rust/skill-grpc
cargo build

echo "=== Compilation completed ==="