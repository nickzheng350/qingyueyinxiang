#!/bin/bash

# HydraFlow AI 部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}   HydraFlow AI 部署脚本${NC}"
echo -e "${GREEN}===========================================${NC}"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装${NC}"
    exit 1
fi

# 创建必要目录
echo -e "${YELLOW}创建必要目录...${NC}"
mkdir -p data logs config deploy/ssl

# 生成SSL证书（如果不存在）
if [ ! -f "deploy/ssl/hydraflow.crt" ]; then
    echo -e "${YELLOW}生成SSL证书...${NC}"
    openssl req -x509 -newkey rsa:4096 -nodes -keyout deploy/ssl/hydraflow.key -out deploy/ssl/hydraflow.crt -days 365 -subj "/CN=hydraflow.local" -quiet
fi

# 构建Docker镜像
echo -e "${YELLOW}构建Docker镜像...${NC}"
docker-compose build --quiet

# 启动服务
echo -e "${YELLOW}启动服务...${NC}"
docker-compose up -d

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo -e "${YELLOW}检查服务状态...${NC}"
docker-compose ps

# 检查健康状态
echo -e "\n${YELLOW}检查健康状态...${NC}"
if curl -s http://localhost/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ 所有服务已成功启动！${NC}"
    echo -e "\n${GREEN}访问地址:${NC}"
    echo -e "  - UI界面: http://localhost"
    echo -e "  - API文档: http://localhost/docs"
    echo -e "  - Grafana: http://localhost:3000 (admin/admin)"
    echo -e "  - Prometheus: http://localhost:9090"
else
    echo -e "${RED}❌ 服务启动失败，请检查日志${NC}"
    docker-compose logs hydraflow-api
    exit 1
fi

echo -e "\n${GREEN}===========================================${NC}"
echo -e "${GREEN}         部署完成！${NC}"
echo -e "${GREEN}===========================================${NC}"
