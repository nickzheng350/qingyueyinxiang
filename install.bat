@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title HydraFlow AI 安装程序

:logo
cls
echo ==============================================
echo        HydraFlow AI - 安装程序
echo ==============================================
echo.

:check_python
echo 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo 找到 Python 版本: !PYTHON_VERSION!

:check_git
echo.
echo 检查 Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 Git，请先安装 Git
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo ✓ Git 已安装

:install_pytorch
echo.
echo 安装 PyTorch...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
if %errorlevel% neq 0 (
    echo 错误: PyTorch 安装失败
    pause
    exit /b 1
)
echo ✓ PyTorch 安装完成

:install_deps
echo.
echo 安装项目依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)
echo ✓ 依赖安装完成

:setup_env
echo.
echo 配置环境...
if not exist .env (
    copy .env.example .env
    echo ✓ .env 文件已创建
)

if not exist "%USERPROFILE%\.hydraflow" (
    mkdir "%USERPROFILE%\.hydraflow"
)

if not exist "%USERPROFILE%\.hydraflow\config.json" (
    copy config\global_config.json "%USERPROFILE%\.hydraflow\config.json"
    echo ✓ 全局配置已复制
)

:install_ui
echo.
echo 安装 UI 依赖...
if exist ui (
    cd ui
    npm install
    cd ..
    echo ✓ UI 依赖安装完成
)

:test
echo.
echo 运行测试...
python main.py diagnose
if %errorlevel% neq 0 (
    echo 警告: 测试未完全通过，请检查日志
) else (
    echo ✓ 测试通过
)

:complete
echo.
echo ==============================================
echo          安装完成！
echo ==============================================
echo.
echo 启动方式:
echo   python main.py
echo   或访问: http://localhost:8000
echo.
pause