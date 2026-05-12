#!/usr/bin/env bash

# HydraFlow AI 一键安装脚本 (Linux/Mac)
# 版本: 2.1.0
# 支持: Ubuntu/Debian/CentOS/Fedora/macOS
# 改进: 添加依赖缓存检查、重试机制、详细错误处理

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

VERSION="2.1.0"
RETRY_MAX=3
RETRY_DELAY=5

show_logo() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "       HydraFlow AI - 安装程序"
    echo "         版本: ${VERSION}"
    echo "=============================================="
    echo -e "${NC}"
}

error_exit() {
    echo -e "${RED}错误: $1${NC}"
    exit 1
}

check_command() {
    local cmd=$1
    local desc=$2
    if ! command -v "$cmd" &> /dev/null; then
        error_exit "未找到 ${desc} (${cmd})，请先安装"
    fi
}

check_dependencies() {
    echo -e "${YELLOW}检查系统依赖...${NC}"

    # 检查 Python 3.10+
    check_command "python3" "Python 3"
    
    # 检查 Python 版本
    local python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    local min_version="3.10"
    if [ $(printf '%s\n' "$min_version" "$python_version" | sort -V | head -n1) != "$min_version" ]; then
        error_exit "Python 版本需要 >= 3.10，当前版本: $python_version"
    fi

    # 检查 Git
    check_command "git" "Git"

    # 检查 pip
    if ! python3 -m pip --version &> /dev/null; then
        error_exit "未找到 pip，请先安装 python3-pip"
    fi

    echo -e "${GREEN}✓ 所有依赖已满足${NC}"
}

install_with_retry() {
    local cmd=$1
    local desc=$2
    local retries=0
    
    echo -e "${YELLOW}安装 ${desc}...${NC}"
    
    while [ $retries -lt $RETRY_MAX ]; do
        if $cmd; then
            echo -e "${GREEN}✓ ${desc} 安装完成${NC}"
            return 0
        fi
        
        retries=$((retries + 1))
        echo -e "${YELLOW}重试第 ${retries}/${RETRY_MAX} 次...${NC}"
        sleep $RETRY_DELAY
    done
    
    error_exit "${desc} 安装失败"
}

install_pytorch() {
    # 检查是否已安装
    if python3 -c "import torch; print(f'PyTorch {torch.__version__}')" &> /dev/null; then
        echo -e "${GREEN}✓ PyTorch 已安装${NC}"
        return 0
    fi
    
    install_with_retry \
        "pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu" \
        "PyTorch"
}

install_dependencies() {
    echo -e "${YELLOW}安装项目依赖...${NC}"
    
    # 检查 requirements.txt 是否存在
    if [ ! -f requirements.txt ]; then
        error_exit "requirements.txt 不存在"
    fi
    
    # 使用缓存安装
    install_with_retry \
        "pip3 install --cache-dir ~/.cache/pip -r requirements.txt" \
        "项目依赖"
}

setup_environment() {
    echo -e "${YELLOW}配置环境变量...${NC}"

    # 创建 .env 文件
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            echo -e "${GREEN}✓ .env 文件已创建${NC}"
        else
            error_exit ".env.example 不存在"
        fi
    else
        echo -e "${YELLOW}提示: .env 文件已存在，跳过创建${NC}"
    fi

    # 创建配置目录
    mkdir -p ~/.hydraflow
    if [ ! -f ~/.hydraflow/config.json ]; then
        if [ -f config/global_config.json ]; then
            cp config/global_config.json ~/.hydraflow/config.json
            echo -e "${GREEN}✓ 全局配置已复制${NC}"
        else
            echo -e "${YELLOW}提示: config/global_config.json 不存在，跳过配置复制${NC}"
        fi
    fi

    # 创建必要目录
    mkdir -p logs
    mkdir -p data/storage
    echo -e "${GREEN}✓ 日志和数据目录已创建${NC}"
}

install_ui_dependencies() {
    echo -e "${YELLOW}安装 UI 依赖...${NC}"
    if [ -d ui ]; then
        if command -v npm &> /dev/null; then
            cd ui && npm install && cd ..
            echo -e "${GREEN}✓ UI 依赖安装完成${NC}"
        else
            echo -e "${YELLOW}提示: 未找到 npm，跳过 UI 依赖安装${NC}"
        fi
    else
        echo -e "${YELLOW}提示: ui 目录不存在，跳过 UI 依赖安装${NC}"
    fi
}

run_tests() {
    echo -e "${YELLOW}运行系统诊断...${NC}"
    if python3 main.py diagnose; then
        echo -e "${GREEN}✓ 诊断通过${NC}"
    else
        echo -e "${YELLOW}警告: 部分诊断项失败，请检查日志${NC}"
    fi
}

print_features() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "       新版本特性 (${VERSION})"
    echo "=============================================="
    echo -e "${NC}"
    echo "✓ 多级缓存优先队列 (L1 LRU + L2 优先级)"
    echo "✓ 同步/异步/并行统一执行框架"
    echo "✓ OpenTelemetry 链路追踪"
    echo "✓ 全局异常处理器"
    echo "✓ 轻量级 RAG 系统"
    echo "✓ 100% 类型提示覆盖"
    echo "✓ 安装脚本增强（重试机制、缓存支持）"
    echo ""
}

main() {
    show_logo
    print_features

    # 检查目录
    if [ ! -f requirements.txt ]; then
        error_exit "请在项目根目录运行此脚本"
    fi

    check_dependencies
    install_pytorch
    install_dependencies
    setup_environment
    install_ui_dependencies
    run_tests

    echo -e "${CYAN}"
    echo "=============================================="
    echo "      ${GREEN}安装完成！${CYAN}"
    echo "=============================================="
    echo -e "${NC}"
    echo "启动方式:"
    echo "  python3 main.py api"
    echo "  或访问: http://localhost:8000"
    echo ""
    echo "其他命令:"
    echo "  python3 main.py diagnose   # 系统诊断"
    echo "  python3 main.py repair     # 自我修复"
    echo ""
}

main "$@"