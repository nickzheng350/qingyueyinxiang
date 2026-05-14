#!/bin/bash
# HydraFlow AI 启动脚本 - 跨平台兼容 (Linux/macOS/Windows WSL)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检测Python环境
detect_python() {
    if [ -f ".venv/bin/python" ]; then
        PYTHON=".venv/bin/python"
    elif [ -f ".venv/Scripts/python.exe" ]; then
        PYTHON=".venv/Scripts/python.exe"
    elif command -v python3 &>/dev/null; then
        PYTHON="python3"
    elif command -v python &>/dev/null; then
        PYTHON="python"
    else
        log_error "未找到Python，请先安装 Python >= 3.10"
        exit 1
    fi
    echo "$PYTHON"
}

PYTHON=$(detect_python)
log_info "使用Python: $PYTHON"

# 创建必要目录
mkdir -p data logs

# 检查依赖
log_info "检查依赖..."
$PYTHON -c "import fastapi, uvicorn, pydantic" 2>/dev/null || {
    log_warn "缺少依赖，正在安装..."
    if [ -f "requirements.txt" ]; then
        $PYTHON -m pip install -q -r requirements.txt 2>/dev/null || true
    fi
}

# 端口配置
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

# 启动服务器
log_info "启动 HydraFlow AI on http://$HOST:$PORT"
$PYTHON -c "
import uvicorn, sys
sys.path.insert(0, '.')
from src.api.app import create_app
app = create_app()
uvicorn.run(app, host='$HOST', port=$PORT, log_level='info')
"