#!/usr/bin/env bash

# HydraFlow AI 一键安装脚本 (Linux/Mac)
# 版本: 1.0.0
# 支持: Ubuntu/Debian/CentOS/Fedora/macOS

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

show_logo() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "       HydraFlow AI - 安装程序"
    echo "=============================================="
    echo -e "${NC}"
}

check_dependencies() {
    echo -e "${YELLOW}检查系统依赖...${NC}"
    
    # 检查 Python 3.10+
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 Python3，请先安装 Python 3.10+${NC}"
        exit 1
    fi
    
    # 检查 Git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}错误: 未找到 Git，请先安装 Git${NC}"
        exit 1
    fi
    
    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 pip3${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 所有依赖已满足${NC}"
}

install_pytorch() {
    echo -e "${YELLOW}安装 PyTorch...${NC}"
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    echo -e "${GREEN}✓ PyTorch 安装完成${NC}"
}

install_dependencies() {
    echo -e "${YELLOW}安装项目依赖...${NC}"
    pip3 install -r requirements.txt
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
}

setup_environment() {
    echo -e "${YELLOW}配置环境变量...${NC}"
    
    # 创建 .env 文件
    if [ ! -f .env ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env 文件已创建${NC}"
    fi
    
    # 创建配置文件
    mkdir -p ~/.hydraflow
    if [ ! -f ~/.hydraflow/config.json ]; then
        cp config/global_config.json ~/.hydraflow/config.json
        echo -e "${GREEN}✓ 全局配置已复制${NC}"
    fi
}

install_ui_dependencies() {
    echo -e "${YELLOW}安装 UI 依赖...${NC}"
    if [ -d ui ]; then
        cd ui && npm install && cd ..
        echo -e "${GREEN}✓ UI 依赖安装完成${NC}"
    fi
}

run_tests() {
    echo -e "${YELLOW}运行测试...${NC}"
    python3 main.py diagnose
    echo -e "${GREEN}✓ 测试通过${NC}"
}

main() {
    show_logo
    
    # 检查目录
    if [ ! -f requirements.txt ]; then
        echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
        exit 1
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
    echo "  python3 main.py"
    echo "  或访问: http://localhost:8000"
    echo ""
}

main "$@"