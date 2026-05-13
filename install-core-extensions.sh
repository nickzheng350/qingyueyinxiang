#!/bin/bash

# HydraFlow AI 核心扩展安装脚本 - 精简版

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}   HydraFlow AI 核心扩展安装${NC}"
echo -e "${BLUE}   最先进技术栈 - 精简版${NC}"
echo -e "${BLUE}===========================================${NC}"

# 激活虚拟环境
source .venv/bin/activate

echo -e "\n${YELLOW}安装核心扩展...${NC}"

# 核心框架
pip install fastapi>=0.104.0 uvicorn[standard]>=0.24.0 pydantic>=2.5.0 pydantic-settings>=2.0.0

# AI/ML核心
pip install torch>=2.1.0 transformers>=4.35.0 accelerate>=0.25.0

# LangChain
pip install langchain>=0.1.0 langchain-community>=0.0.10 openai>=1.3.0

# 向量数据库
pip install chromadb>=0.4.18 faiss-cpu>=1.7.4

# 图像处理
pip install Pillow>=10.0.0 opencv-python>=4.8.0

# 数据库
pip install sqlalchemy>=2.0.23 asyncpg>=0.29.0 redis>=5.0.0

# 异步
pip install aiohttp>=3.9.0 httpx>=0.25.0 aiofiles>=23.2.1

# 监控
pip install prometheus-client>=0.19.0 sentry-sdk>=1.39.0

# 安全
pip install python-jose>=3.3.0 passlib>=1.7.4 bcrypt>=4.1.0

# 工具
pip install python-dotenv>=1.0.0 python-multipart>=0.0.6

echo -e "\n${GREEN}✅ 核心扩展安装完成！${NC}"
echo -e "\n${BLUE}已安装的核心扩展：${NC}"
echo -e "  🚀 FastAPI + Uvicorn"
echo -e "  🤗 PyTorch + Transformers"
echo -e "  🔗 LangChain"
echo -e "  🔍 ChromaDB + FAISS"
echo -e "  🖼️ OpenCV + Pillow"
echo -e "  💾 PostgreSQL + Redis"
echo -e "  ⚡ AsyncIO + HTTPX"
echo -e "  📊 Prometheus + Sentry"
echo -e "  🔐 JWT + Bcrypt"
