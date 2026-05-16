# HydraFlow AI 项目部署指南

## 目录

1. [前置准备](#前置准备)
2. [环境要求](#环境要求)
3. [后端部署](#后端部署)
4. [前端部署](#前端部署)
5. [配置说明](#配置说明)
6. [启动服务](#启动服务)
7. [健康检查](#健康检查)
8. [常见问题](#常见问题)

---

## 前置准备

### 1.1 获取代码

```bash
# 克隆仓库
git clone <仓库地址>
cd nick

# 切换到生产分支
git checkout main
git pull origin main
```

### 1.2 环境变量配置

复制 `.env.example` 到 `.env` 并修改配置：

```bash
cp .env.example .env
vim .env
```

关键配置项：

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `API_HOST` | API 服务地址 | `0.0.0.0` |
| `API_PORT` | API 服务端口 | `8000` |
| `DB_HOST` | 数据库地址 | `localhost` |
| `DB_PORT` | 数据库端口 | `5432` |
| `DB_NAME` | 数据库名称 | `hydraflow` |
| `DB_USER` | 数据库用户名 | `postgres` |
| `DB_PASSWORD` | 数据库密码 | `password` |

---

## 环境要求

### 2.1 系统要求

| 项目 | 版本 |
|------|------|
| Python | >= 3.10 |
| Node.js | >= 18.0 |
| npm | >= 9.0 |
| PostgreSQL | >= 14.0 (可选) |

### 2.2 安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd ui
npm install
cd ..
```

---

## 后端部署

### 3.1 数据库初始化（可选）

如果使用 PostgreSQL：

```bash
# 创建数据库
createdb -U postgres hydraflow

# 运行迁移（如果有）
alembic upgrade head
```

### 3.2 构建后端

```bash
# 确保虚拟环境已激活
source .venv/bin/activate

# 运行构建脚本
python setup.py build
```

---

## 前端部署

### 4.1 构建前端

```bash
cd ui

# 开发环境构建
npm run dev

# 生产环境构建
npm run build

# 构建产物位于 ui/dist 目录
```

### 4.2 配置 Nginx（推荐）

创建 `/etc/nginx/sites-available/hydraflow.conf`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/nick/ui/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置：

```bash
ln -s /etc/nginx/sites-available/hydraflow.conf /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## 配置说明

### 5.1 后端配置文件

配置文件位于 `config/settings.yaml`：

```yaml
api:
  host: 0.0.0.0
  port: 8000
  docs_enabled: false  # 生产环境建议关闭

security:
  cors_origins:
    - https://your-domain.com
  rate_limit: 1000/hour

storage:
  data_dir: ./data
  skills_dir: ./skills

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### 5.2 前端环境变量

创建 `ui/.env.production`：

```env
VITE_API_URL=/api
VITE_WS_URL=/ws
VITE_APP_TITLE=HydraFlow AI
```

---

## 启动服务

### 6.1 使用 systemd（推荐）

创建 `/etc/systemd/system/hydraflow.service`：

```ini
[Unit]
Description=HydraFlow AI Service
After=network.target

[Service]
User=hydraflow
Group=hydraflow
WorkingDirectory=/path/to/nick
Environment="PATH=/path/to/nick/.venv/bin"
ExecStart=/path/to/nick/.venv/bin/python -m uvicorn src.api.app:create_app --host 0.0.0.0 --port 8000 --workers 4 --factory
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 创建专用用户
useradd -r -s /usr/sbin/nologin hydraflow
chown -R hydraflow:hydraflow /path/to/nick

# 启动服务
systemctl daemon-reload
systemctl enable hydraflow
systemctl start hydraflow
```

### 6.2 使用 Docker（可选）

构建 Docker 镜像：

```bash
docker build -t hydraflow:latest .

# 运行容器
docker run -d \
  --name hydraflow \
  -p 8000:8000 \
  -v /path/to/data:/app/data \
  -v /path/to/skills:/app/skills \
  --env-file .env \
  hydraflow:latest
```

---

## 健康检查

### 7.1 检查服务状态

```bash
# 检查后端服务
curl -f http://localhost:8000/api/v1/health

# 检查前端
curl -f http://localhost:80/

# 检查日志
journalctl -u hydraflow -f
```

### 7.2 预期响应

**健康检查接口** (`/api/v1/health`)：

```json
{
  "status": "healthy",
  "version": "1.1.0",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 常见问题

### 8.1 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

### 8.2 权限问题

```bash
# 确保数据目录有写入权限
chown -R hydraflow:hydraflow /path/to/nick/data
chmod -R 755 /path/to/nick/data
```

### 8.3 内存不足

调整 uvicorn worker 数量：

```bash
# 在 systemd 配置中修改
ExecStart=/path/to/nick/.venv/bin/python -m uvicorn src.api.app:create_app --host 0.0.0.0 --port 8000 --workers 2 --factory
```

### 8.4 前端静态资源 404

确保 Nginx 配置中的 root 路径正确指向 `ui/dist` 目录。

---

## 备份与恢复

### 数据备份

```bash
# 备份数据库
pg_dump -U postgres hydraflow > backup.sql

# 备份技能目录
tar -czvf skills_backup.tar.gz skills/
```

### 数据恢复

```bash
# 恢复数据库
psql -U postgres hydraflow < backup.sql

# 恢复技能目录
tar -xzvf skills_backup.tar.gz
```

---

## 更新部署

```bash
# 停止服务
systemctl stop hydraflow

# 更新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重新构建前端
cd ui && npm install && npm run build && cd ..

# 启动服务
systemctl start hydraflow
```

---

**文档版本**: v1.1.0  
**更新日期**: 2026年5月  
**适用项目**: HydraFlow AI