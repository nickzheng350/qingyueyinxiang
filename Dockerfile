# HydraFlow AI 服务镜像
#
# 默认安装 requirements-dev.txt（轻量集，可启动 API 与运行测试）。
# 如果需要多模态推理能力（torch / transformers / opencv），
# 把下面的 requirements-dev.txt 换成 requirements.txt，镜像体积会显著变大。

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /app

# 单独 COPY 依赖清单，最大化利用构建缓存
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements-dev.txt

COPY . .

# 数据库初始化（SQLite 场景），失败不阻断构建
RUN python -c "import asyncio; \
    from src.persistence.database import init_db; \
    asyncio.run(init_db())" || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request, sys; \
        sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status == 200 else 1)"

CMD ["python", "main.py", "api", "--host", "0.0.0.0", "--port", "8000"]
