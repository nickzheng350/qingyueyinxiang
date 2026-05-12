#!/usr/bin/env bash

# HydraFlow AI 部署脚本 v2.0
# 安全加固版本 - 包含安全检查和验证

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31M'
NC='\033[0m'

VERSION="2.0.0"

show_logo() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "      HydraFlow AI - 部署脚本"
    echo "         版本: ${VERSION}"
    echo "=============================================="
    echo -e "${NC}"
}

error_exit() {
    echo -e "${RED}错误: $1${NC}"
    exit 1
}

check_git() {
    echo -e "${YELLOW}检查 Git 配置...${NC}"
    
    if ! command -v git &> /dev/null; then
        error_exit "未找到 Git"
    fi
    
    if [ ! -d .git ]; then
        echo -e "${YELLOW}初始化 Git 仓库...${NC}"
        git init
        git config user.name "HydraFlow AI"
        git config user.email "dev@hydraflow.ai"
    fi
    
    echo -e "${GREEN}✓ Git 配置完成${NC}"
}

run_security_check() {
    echo -e "${YELLOW}运行安全检查...${NC}"
    
    if [ -f scripts/security_check.py ]; then
        python3 scripts/security_check.py
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}警告: 安全检查发现问题，建议修复后再部署${NC}"
            read -p "是否继续部署？(y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                error_exit "部署已取消"
            fi
        fi
    else
        echo -e "${YELLOW}安全检查脚本不存在，跳过${NC}"
    fi
    
    echo -e "${GREEN}✓ 安全检查完成${NC}"
}

check_sensitive_files() {
    echo -e "${YELLOW}检查敏感文件...${NC}"
    
    SENSITIVE_FILES=(
        ".env"
        "*.key"
        "*.pem"
        "secrets/"
        "credentials/"
    )
    
    for pattern in "${SENSITIVE_FILES[@]}"; do
        if find . -name "$pattern" -type f 2>/dev/null | grep -v ".git" | grep -q .; then
            echo -e "${RED}警告: 发现可能的敏感文件: $pattern${NC}"
            echo "  请确保这些文件已在 .gitignore 中"
        fi
    done
    
    echo -e "${GREEN}✓ 敏感文件检查完成${NC}"
}

check_gitignore() {
    echo -e "${YELLOW}检查 .gitignore 配置...${NC}"
    
    REQUIRED_PATTERNS=(
        ".env"
        "*.key"
        "*.pem"
        "secrets/"
        "*.log"
        "__pycache__"
    )
    
    if [ ! -f .gitignore ]; then
        error_exit ".gitignore 文件不存在"
    fi
    
    for pattern in "${REQUIRED_PATTERNS[@]}"; do
        if ! grep -q "^${pattern}" .gitignore && ! grep -q "^${pattern}" .gitignore; then
            echo -e "${YELLOW}警告: .gitignore 缺少: ${pattern}${NC}"
        fi
    done
    
    echo -e "${GREEN}✓ .gitignore 检查完成${NC}"
}

update_version() {
    echo -e "${YELLOW}更新版本号...${NC}"
    
    # 更新 README.md 中的版本
    if [ -f README.md ]; then
        sed -i "s/v[0-9]\+\.[0-9]\+\.[0-9]\+/v${VERSION}/g" README.md
    fi
    
    # 更新 main.py 中的版本
    if [ -f main.py ]; then
        sed -i "s/version = \"[0-9]\+\.[0-9]\+\.[0-9]\+\"/version = \"${VERSION}\"/g" main.py
    fi
    
    echo -e "${GREEN}✓ 版本号更新完成${NC}"
}

build_package() {
    echo -e "${YELLOW}构建安装包...${NC}"
    
    # 清理旧的构建
    rm -rf dist/
    mkdir -p dist
    
    # 复制必要文件
    cp -r src/ dist/
    cp -r config/ dist/ 2>/dev/null || true
    cp -r prompts/ dist/ 2>/dev/null || true
    cp -r docs/ dist/ 2>/dev/null || true
    cp -r skills/ dist/ 2>/dev/null || true
    cp -r scripts/ dist/ 2>/dev/null || true
    cp requirements.txt dist/
    cp setup.py dist/ 2>/dev/null || true
    cp pyproject.toml dist/ 2>/dev/null || true
    cp main.py dist/
    cp install.sh dist/
    cp .env.example dist/
    
    # 创建 README
    cat > dist/README.md << 'EOF'
# HydraFlow AI 安装包

## 快速开始

### Linux/Mac
```bash
chmod +x install.sh
./install.sh
```

### Windows
```cmd
install.bat
```

## 启动服务

```bash
python3 main.py api
```

访问 http://localhost:8000

## 更多信息

- 文档: https://docs.hydraflow.ai
- GitHub: https://github.com/hydraflow-ai/hydraflow
EOF
    
    # 打包
    cd dist && zip -r ../hydraflow-ai-${VERSION}.zip . && cd ..
    
    echo -e "${GREEN}✓ 安装包构建完成: hydraflow-ai-${VERSION}.zip${NC}"
}

commit_changes() {
    echo -e "${YELLOW}提交更改...${NC}"
    
    # 检查是否有更改
    if [ -z "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}没有需要提交的更改${NC}"
        return 0
    fi
    
    # 添加所有文件
    git add -A
    
    # 提交
    git commit -m "Release: HydraFlow AI v${VERSION}

- 安全加固：添加认证、授权、速率限制
- 新增安全中间件：输入验证、XSS/SQL注入防护
- 更新 .gitignore：防止敏感文件泄露
- 添加安全检查脚本：自动化安全审计
- 完善文档：安全指南和最佳实践
- 修复循环导入问题
- 优化安装部署脚本"

    echo -e "${GREEN}✓ 更改已提交${NC}"
}

push_to_github() {
    echo -e "${YELLOW}推送到 GitHub...${NC}"
    
    # 检查远程仓库
    if ! git remote get-url origin &> /dev/null; then
        echo -e "${YELLOW}未配置远程仓库${NC}"
        echo "请手动添加远程仓库："
        echo "  git remote add origin https://github.com/yourusername/hydraflow-ai.git"
        return 0
    fi
    
    # 推送到 main 分支
    git push origin main
    
    echo -e "${GREEN}✓ 已推送到 GitHub${NC}"
}

create_release_notes() {
    cat > RELEASE_NOTES.md << EOF
# HydraFlow AI v${VERSION} 发布说明

## 新增功能

### 安全加固
- ✨ 添加 JWT 认证和授权系统
- ✨ 实现基于角色的访问控制（RBAC）
- ✨ 添加速率限制，防止暴力破解和 DDoS
- ✨ 实现安全头中间件（CSP, HSTS, X-Frame-Options）
- ✨ 添加输入验证中间件，防止 SQL 注入和 XSS
- ✨ 创建安全检查脚本，自动化安全审计

### 开发体验
- ✨ 创建 setup.py 和 pyproject.toml，支持 pip 安装
- ✨ 优化安装脚本，添加重试机制和依赖检查
- ✨ 修复循环导入问题
- ✨ 统一配置系统入口

## 安全改进

- 🔒 所有 API 端点需要认证（除登录/注册）
- 🔒 管理操作需要管理员权限
- 🔒 密码使用 bcrypt 哈希（salt rounds = 12）
- 🔒 JWT 令牌有效期限制
- 🔒 CORS 配置限制为已知域名
- 🔒 更新 .gitignore，防止敏感文件泄露

## Bug 修复

- 🐛 修复循环导入导致的启动错误
- 🐛 修复未使用导入（F401 错误）
- 🐛 修复配置系统不一致问题

## 文档

- 📝 添加安全加固指南（docs/SECURITY.md）
- 📝 更新 README.md
- 📝 添加部署文档

## 安装

\`\`\`bash
# 克隆仓库
git clone https://github.com/hydraflow-ai/hydraflow.git
cd hydraflow

# 运行安装脚本
chmod +x install.sh
./install.sh

# 启动服务
python3 main.py api
\`\`\`

## 升级

\`\`\`bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install --upgrade -r requirements.txt

# 重启服务
\`\`\`

## 安全提示

⚠️ 部署前请务必：
1. 修改 .env 中的 JWT_SECRET_KEY
2. 配置正确的 CORS_ORIGINS
3. 启用 HTTPS
4. 运行安全检查脚本

## 已知问题

无

## 贡献者

- HydraFlow AI Team

## 许可证

MIT License
EOF
    
    echo -e "${GREEN}✓ 发布说明已创建${NC}"
}

main() {
    show_logo
    
    check_git
    run_security_check
    check_sensitive_files
    check_gitignore
    update_version
    build_package
    commit_changes
    push_to_github
    create_release_notes
    
    echo -e "${CYAN}"
    echo "=============================================="
    echo "      ${GREEN}部署完成！${CYAN}"
    echo "=============================================="
    echo -e "${NC}"
    echo "项目已准备就绪，包含："
    echo "  - 安装包: hydraflow-ai-${VERSION}.zip"
    echo "  - 安全检查脚本"
    echo "  - 安全文档"
    echo "  - 发布说明: RELEASE_NOTES.md"
    echo ""
    echo "下一步："
    echo "  1. 上传安装包到 GitHub Releases"
    echo "  2. 更新文档网站"
    echo "  3. 通知用户更新"
    echo ""
}

main "$@"
