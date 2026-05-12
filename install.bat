@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title HydraFlow AI 安装程序
set VERSION=2.0.0

:logo
cls
echo ==============================================
echo        HydraFlow AI - 安装程序
echo          版本: %VERSION%
echo ==============================================
echo.

:print_features
echo 新版本特性:
echo   - 多级缓存优先队列 (L1 LRU + L2 优先级)
echo   - 同步/异步/并行统一执行框架
echo   - OpenTelemetry 链路追踪
echo   - 全局异常处理器
echo   - 轻量级 RAG 系统
echo   - 100%% 类型提示覆盖
echo.
echo ==============================================
echo.

:check_python
echo [1/7] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   错误: 未找到 Python，请先安装 Python 3.10+
    echo   下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo   ✓ 找到 Python: !PYTHON_VERSION!

:check_git
echo.
echo [2/7] 检查 Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   错误: 未找到 Git，请先安装 Git
    echo   下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo   ✓ Git 已安装

:install_pytorch
echo.
echo [3/7] 安装 PyTorch...
pip install torch torchvision torchaudio ^
    --index-url https://download.pytorch.org/whl/cpu
if %errorlevel% neq 0 (
    echo   错误: PyTorch 安装失败
    pause
    exit /b 1
)
echo   ✓ PyTorch 安装完成

:install_deps
echo.
echo [4/7] 安装项目依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo   错误: 依赖安装失败
    pause
    exit /b 1
)
echo   ✓ 依赖安装完成

:setup_env
echo.
echo [5/7] 配置环境...
if not exist .env (
    copy .env.example .env
    echo   ✓ .env 文件已创建
)

if not exist "%USERPROFILE%\.hydraflow" (
    mkdir "%USERPROFILE%\.hydraflow"
)

if not exist "%USERPROFILE%\.hydraflow\config.json" (
    copy config\global_config.json "%USERPROFILE%\.hydraflow\config.json"
    echo   ✓ 全局配置已复制
)

if not exist "logs" (
    mkdir logs
    echo   ✓ 日志目录已创建
)

:install_ui
echo.
echo [6/7] 安装 UI 依赖...
if exist ui (
    cd ui
    npm install
    cd ..
    echo   ✓ UI 依赖安装完成
) else (
    echo   - UI 目录不存在，跳过
)

:test
echo.
echo [7/7] 运行测试...
python main.py diagnose
if %errorlevel% neq 0 (
    echo   警告: 测试未完全通过，请检查日志
) else (
    echo   ✓ 测试通过
)

:complete
echo.
echo ==============================================
echo          安装完成！ (%VERSION%)
echo ==============================================
echo.
echo 启动方式:
echo   python main.py
echo   或访问: http://localhost:8000
echo.
pause
