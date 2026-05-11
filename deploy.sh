#!/usr/bin/env bash

# HydraFlow AI 部署脚本
# 用于打包和推送项目到 GitHub

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

show_logo() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "      HydraFlow AI - 部署脚本"
    echo "=============================================="
    echo -e "${NC}"
}

check_git() {
    echo -e "${YELLOW}检查 Git 配置...${NC}"
    
    if ! command -v git &> /dev/null; then
        echo -e "${RED}错误: 未找到 Git${NC}"
        exit 1
    fi
    
    # 检查是否在 git 仓库中
    if [ ! -d .git ]; then
        echo -e "${YELLOW}初始化 Git 仓库...${NC}"
        git init
        git config user.name "HydraFlow AI"
        git config user.email "dev@hydraflow.ai"
    fi
    
    echo -e "${GREEN}✓ Git 配置完成${NC}"
}

update_gitignore() {
    echo -e "${YELLOW}更新 .gitignore...${NC}"
    
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.venv/
.env

# 模型文件
models/
*.bin
*.safetensors
*.ckpt

# 日志
*.log
logs/

# 缓存
.cache/
*.pkl

# 编辑器
.vscode/
.idea/
*.swp
*.swo
*~

# 系统
.DS_Store
Thumbs.db

# 构建
dist/
build/
*.egg-info/

# 测试
test_*.py
.pytest_cache/

# Node.js
node_modules/
package-lock.json
EOF
    
    echo -e "${GREEN}✓ .gitignore 更新完成${NC}"
}

build_package() {
    echo -e "${YELLOW}构建安装包...${NC}"
    
    # 创建打包目录
    mkdir -p dist
    
    # 复制必要文件
    cp -r src/ dist/
    cp -r config/ dist/
    cp -r prompts/ dist/
    cp -r docs/ dist/
    cp -r skills/ dist/
    cp requirements.txt dist/
    cp main.py dist/
    cp install.sh dist/
    cp install.bat dist/
    cp README.md dist/
    cp LICENSE dist/
    cp .env.example dist/
    
    # 打包
    cd dist && zip -r hydraflow-ai.zip . && cd ..
    mv dist/hydraflow-ai.zip .
    
    echo -e "${GREEN}✓ 安装包构建完成${NC}"
}

push_to_github() {
    echo -e "${YELLOW}推送到 GitHub...${NC}"
    
    # 添加所有文件
    git add -A
    
    # 提交
    git commit -m "Release: HydraFlow AI v1.0.0"
    
    # 推送到 main 分支
    git push origin main
    
    echo -e "${GREEN}✓ 已推送到 GitHub${NC}"
}

main() {
    show_logo
    
    check_git
    update_gitignore
    build_package
    
    echo -e "${CYAN}"
    echo "=============================================="
    echo "      ${GREEN}部署完成！${CYAN}"
    echo "=============================================="
    echo -e "${NC}"
    echo "项目已准备就绪，包含："
    echo "  - 一键安装脚本 (install.sh / install.bat)"
    echo "  - 完整依赖列表 (requirements.txt)"
    echo "  - 安装包 (hydraflow-ai.zip)"
    echo ""
    echo "推送到 GitHub:"
    echo "  git remote add origin https://github.com/yourusername/hydraflow-ai.git"
    echo "  git push -u origin main"
    echo ""
}

main "$@"