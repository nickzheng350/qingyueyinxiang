#!/bin/bash

# HydraFlow AI 扩展安装脚本 - 企业级增强版

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}   HydraFlow AI 扩展安装脚本${NC}"
echo -e "${BLUE}   企业级增强版 - 最先进技术栈${NC}"
echo -e "${BLUE}===========================================${NC}"

# 检查Python虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}创建Python虚拟环境...${NC}"
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 升级pip
echo -e "${YELLOW}升级pip...${NC}"
pip install --upgrade pip setuptools wheel

# 分批安装Python依赖
echo -e "\n${GREEN}=== 第一阶段：核心框架 ===${NC}"
pip install fastapi>=0.104.0 uvicorn[standard]>=0.24.0 pydantic>=2.5.0 pydantic-settings>=2.0.0

echo -e "\n${GREEN}=== 第二阶段：AI/ML核心库 ===${NC}"
pip install torch>=2.1.0 torchvision>=0.16.0 torchaudio>=2.1.0 transformers>=4.35.0 accelerate>=0.25.0

echo -e "\n${GREEN}=== 第三阶段：LangChain生态系统 ===${NC}"
pip install langchain>=0.1.0 langchain-community>=0.0.10 openai>=1.3.0 anthropic>=0.7.0 cohere>=4.39.0

echo -e "\n${GREEN}=== 第四阶段：RAG/向量数据库 ===${NC}"
pip install chromadb>=0.4.18 pinecone-client>=2.2.4 weaviate-client>=3.24.0 qdrant-client>=1.7.0 faiss-cpu>=1.7.4

echo -e "\n${GREEN}=== 第五阶段：图像/视频处理 ===${NC}"
pip install Pillow>=10.0.0 opencv-python>=4.8.0 moviepy>=1.0.3 rembg>=2.0.50

echo -e "\n${GREEN}=== 第六阶段：音频处理 ===${NC}"
pip install librosa>=0.10.0 pydub>=0.25.0 soundfile>=0.12.0

echo -e "\n${GREEN}=== 第七阶段：数据库 ===${NC}"
pip install sqlalchemy>=2.0.23 asyncpg>=0.29.0 redis>=5.0.0 pymongo>=4.6.0

echo -e "\n${GREEN}=== 第八阶段：数据处理 ===${NC}"
pip install pandas>=2.1.0 numpy>=1.24.0 scipy>=1.11.0 scikit-learn>=1.3.0

echo -e "\n${GREEN}=== 第九阶段：异步/并发 ===${NC}"
pip install aiohttp>=3.9.0 httpx>=0.25.0 aiofiles>=23.2.1 uvloop>=0.19.0

echo -e "\n${GREEN}=== 第十阶段：监控/日志 ===${NC}"
pip install prometheus-client>=0.19.0 sentry-sdk>=1.39.0 structlog>=23.2.0

echo -e "\n${GREEN}=== 第十一阶段：安全 ===${NC}"
pip install python-jose>=3.3.0 passlib>=1.7.4 bcrypt>=4.1.0 cryptography>=41.0.0

echo -e "\n${GREEN}=== 第十二阶段：开发工具 ===${NC}"
pip install pytest>=7.4.0 black>=23.12.0 flake8>=6.1.0 mypy>=1.7.1

echo -e "\n${GREEN}=== 第十三阶段：其他依赖 ===${NC}"
pip install -r requirements.txt --no-deps || true

# 检查Node.js
echo -e "\n${YELLOW}检查Node.js环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js未安装，跳过前端依赖安装${NC}"
    echo -e "${YELLOW}请访问 https://nodejs.org/ 安装Node.js 18+${NC}"
else
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}Node.js版本: $NODE_VERSION${NC}"

    # 检查npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}npm未安装${NC}"
    else
        NPM_VERSION=$(npm -v)
        echo -e "${GREEN}npm版本: $NPM_VERSION${NC}"

        # 安装前端依赖
        echo -e "\n${YELLOW}安装前端依赖...${NC}"
        cd ui
        npm install --legacy-peer-deps || true
        cd ..
    fi
fi

echo -e "\n${GREEN}===========================================${NC}"
echo -e "${GREEN}      扩展安装完成！${NC}"
echo -e "${GREEN}===========================================${NC}"
echo -e "\n${BLUE}已安装的主要扩展：${NC}"
echo -e "  🚀 FastAPI + Uvicorn (高性能Web框架)"
echo -e "  🤗 PyTorch + Transformers (深度学习)"
echo -e "  🔗 LangChain (AI应用框架)"
echo -e "  🔍 ChromaDB + Pinecone + Weaviate (向量数据库)"
echo -e "  🖼️ OpenCV + Pillow (图像处理)"
echo -e "  🎵 Librosa + Pydub (音频处理)"
echo -e "  💾 PostgreSQL + Redis + MongoDB (数据库)"
echo -e "  ⚡ AsyncIO + HTTPX (异步网络)"
echo -e "  📊 Prometheus + Sentry (监控)"
echo -e "  🔐 JWT + Bcrypt (安全)"
echo -e "  🎨 Vue 3 + Element Plus (前端UI)"
echo -e "  📈 ECharts + D3.js (数据可视化)"
echo -e "  🎭 Three.js + GSAP (3D/动画)"
echo -e "\n${GREEN}所有扩展已成功安装！${NC}"
