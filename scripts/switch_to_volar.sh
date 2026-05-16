#!/bin/bash

# ================================================
# 一键切换到 Volar 插件脚本
# ================================================
# 功能：禁用 Vetur 插件并安装启用 Volar 插件
# 适用于 VS Code 环境
# ================================================

set -e

echo "================================================"
echo "  正在切换 Vue 开发环境：Vetur → Volar"
echo "================================================"
echo ""

# 检查是否安装了 code 命令
if ! command -v code &> /dev/null; then
    echo "❌ 错误：未找到 code 命令，请确保 VS Code 已正确安装并添加到 PATH"
    echo "   在 VS Code 中按 Ctrl+Shift+P，输入 'shell command'，选择 'Install 'code' command in PATH'"
    exit 1
fi

echo "1️⃣ 禁用 Vetur 插件..."
code --disable-extension octref.vetur

echo "2️⃣ 安装 Volar 插件..."
code --install-extension Vue.volar

echo "3️⃣ 安装 TypeScript Vue Plugin (Volar)..."
code --install-extension Vue.vscode-typescript-vue-plugin

echo ""
echo "================================================"
echo "✅ 切换完成！"
echo "================================================"
echo ""
echo "📋 后续操作："
echo "   1. 重启 VS Code"
echo "   2. 在项目根目录创建/更新 jsconfig.json 或 tsconfig.json"
echo "   3. 确保文件包含路径别名配置："
echo ""
echo "   {\n     \"compilerOptions\": {\n       \"baseUrl\": \".\",\n       \"paths\": {\n         \"@/*\": [\"src/*\"]\n       }\n     }\n   }"
echo ""
echo "💡 提示：Volar 会自动检测 Vue 文件并提供正确的类型支持"
echo "   如果仍然遇到类型问题，请尝试："
echo "   - 执行 Ctrl+Shift+P → Vue: Restart Vue Language Server"
echo "   - 删除 .vscode/.volar 目录后重启 VS Code"