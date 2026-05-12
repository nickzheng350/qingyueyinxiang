# HydraFlow AI 网络链接功能报告

**生成日期**: 2026-05-12
**功能模块**: 网络下载与 HTTP 客户端

---

## 📋 功能概述

### 已实现功能

#### 1. **下载管理器** (`src/network/download.py`)

完整的文件下载解决方案，支持：

- ✅ **多线程/异步下载** - 使用 httpx 异步流式下载
- ✅ **断点续传** - 支持暂停/恢复下载
- ✅ **进度跟踪** - 实时回调下载进度
- ✅ **重试机制** - 自动重试失败下载
- ✅ **哈希验证** - 下载后验证文件完整性
- ✅ **SSL 验证** - 支持跳过 SSL 验证
- ✅ **进度百分比** - 实时显示下载速度和进度

**核心类**:
- `DownloadManager` - 下载管理器单例
- `DownloadTask` - 下载任务配置
- `DownloadProgress` - 下载进度信息
- `ModelDownloader` - 模型下载器（支持 HuggingFace/ModelScope）
- `SkillDownloader` - 技能包下载器

#### 2. **HTTP 客户端** (`src/network/client.py`)

统一的 HTTP 客户端封装，提供：

- ✅ **自动重试** - 请求失败自动重试
- ✅ **超时控制** - 可配置连接和读取超时
- ✅ **连接池** - 高效的连接复用
- ✅ **重定向跟随** - 自动跟随 HTTP 重定向
- ✅ **JSON 解析** - 自动解析 JSON 响应

**核心类**:
- `HTTPClient` - 底层 HTTP 客户端
- `APIClient` - API 客户端基类
- `OpenAIClient` - OpenAI API 客户端
- `AnthropicClient` - Anthropic API 客户端
- `StabilityAIClient` - Stability AI API 客户端

---

## 🔗 内置网络链接

### API 端点配置

| 服务 | Base URL | 用途 |
|------|----------|------|
| **OpenAI** | `https://api.openai.com/v1` | GPT 模型调用 |
| **Anthropic** | `https://api.anthropic.com/v1` | Claude 模型调用 |
| **Stability AI** | `https://api.stability.ai/v1` | 图像生成 |
| **LM Studio** | `http://localhost:1234/v1` | 本地 LLM |
| **Ollama** | `http://localhost:11434/v1` | 本地 LLM |
| **HuggingFace** | `https://huggingface.co` | 模型托管/下载 |
| **ModelScope** | `https://www.modelscope.cn` | 国内模型托管 |
| **技能市场** | `https://hydraflow-ai.org/market/api/v1` | 技能包下载 |
| **PyTorch** | `https://download.pytorch.org/whl` | PyTorch 包下载 |

### 配置文件

**路径**: `config/network_endpoints.json`

包含所有内置 API 端点、重试策略、超时设置等配置。

---

## 🚀 使用示例

### 1. 基础文件下载

```python
from src.network import get_download_manager, DownloadProgress

async def progress_handler(progress: DownloadProgress):
    print(f"下载进度: {progress.progress_str}")

manager = get_download_manager()
file_path = await manager.download(
    url="https://example.com/file.zip",
    destination="./downloads",
    filename="file.zip",
    progress_callback=progress_handler,
)
print(f"文件已下载到: {file_path}")
```

### 2. 模型下载

```python
from src.network import get_model_downloader

downloader = get_model_downloader()

# 从 HuggingFace 下载模型
model_path = await downloader.download_model(
    model_id="stabilityai/stable-diffusion-xl-base-1.0",
    source="huggingface",
    destination="./models",
)

# 从 ModelScope 下载模型
model_path = await downloader.download_model(
    model_id="AI-ModelScope/stable-diffusion-v1-4",
    source="modelscope",
    destination="./models",
)
```

### 3. 技能包下载

```python
from src.network import get_skill_downloader

downloader = get_skill_downloader()

# 下载技能包
skill_path = await downloader.download_skill(
    skill_id="image-enhancer",
    version="1.0.0",
    destination="./skills",
)

# 列出市场技能
skills = await downloader.list_market_skills(category="image")
```

### 4. API 调用

```python
from src.network import OpenAIClient

client = OpenAIClient(api_key="your-api-key")

# 发送聊天请求
response = await client.post("/chat/completions", json={
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
})

if response.ok:
    data = response.json
    print(data["choices"][0]["message"]["content"])
```

### 5. 暂停/恢复下载

```python
from src.network import get_download_manager

manager = get_download_manager()
url = "https://example.com/large-file.zip"

# 开始下载
task = await manager.download(url, destination="./downloads")

# 暂停
await manager.pause(url)

# 恢复
await manager.resume_download(url)

# 取消
await manager.cancel(url)
```

---

## 📊 内置链接清单

### API 服务

```json
{
  "openai": "https://api.openai.com/v1",
  "anthropic": "https://api.anthropic.com/v1",
  "stability_ai": "https://api.stability.ai/v1",
  "lm_studio": "http://localhost:1234/v1",
  "ollama": "http://localhost:11434/v1"
}
```

### 模型下载

```json
{
  "huggingface": "https://huggingface.co/{model_id}/resolve/main/{filename}",
  "modelscope": "https://www.modelscope.cn/{model_id}/resolve/master/{filename}",
  "pytorch_cpu": "https://download.pytorch.org/whl/cpu/torch",
  "pytorch_cuda": "https://download.pytorch.org/whl/cu118/torch"
}
```

### 技能市场

```json
{
  "market_api": "https://hydraflow-ai.org/market/api/v1",
  "list_skills": "/skills",
  "download": "/skills/{skill_id}/versions/{version}/download"
}
```

---

## ⚙️ 配置选项

### 下载设置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `chunk_size` | 8192 | 每次读取的字节数 |
| `max_retries` | 3 | 最大重试次数 |
| `retry_delay` | 5 | 重试延迟（秒） |
| `timeout` | 300 | 下载超时（秒） |
| `resume` | true | 是否支持断点续传 |
| `verify_ssl` | true | 是否验证 SSL |

### HTTP 客户端设置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `timeout` | 30.0 | 请求超时（秒） |
| `max_retries` | 3 | 最大重试次数 |
| `retry_delay` | 1.0 | 初始重试延迟（秒） |
| `backoff_multiplier` | 2.0 | 退避倍数 |
| `max_keepalive` | 20 | 保持连接数 |
| `max_connections` | 100 | 最大连接数 |

---

## 🔧 技术实现

### 异步下载流程

```
1. 创建下载任务
   ↓
2. 检查已下载文件（断点续传）
   ↓
3. 发送 HTTP GET 请求（带 Range 头）
   ↓
4. 流式读取响应内容
   ↓
5. 写入文件并更新进度
   ↓
6. 验证文件哈希（如配置）
   ↓
7. 返回下载完成路径
```

### 重试策略

```
首次失败 → 等待 1s → 重试
第二次失败 → 等待 2s → 重试
第三次失败 → 等待 4s → 重试
第四次失败 → 放弃并抛出异常
```

---

## 📝 依赖项

已在 `requirements.txt` 中配置：

```
httpx>=0.25.0      # 异步 HTTP 客户端
requests>=2.31.0   # 同步 HTTP 客户端
aiohttp>=3.9.1     # 异步 HTTP（备选）
certifi>=2023.11.17 # SSL 证书验证
```

---

## 🎯 下一步计划

1. **集成到任务引擎** - 将下载功能集成到任务执行流程
2. **缓存机制** - 添加下载缓存避免重复下载
3. **并发控制** - 限制同时下载任务数量
4. **下载队列** - 支持批量下载队列
5. **CDN 支持** - 添加 CDN 回源和多源下载

---

**结论**: 所有基础下载功能已内置实现 ✅
