# HydraFlow AI 系统架构文档

## 项目概述

HydraFlow AI 是一个生成式工作流平台，提供统一的接口来管理和执行各种AI模型任务。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  REST API (FastAPI)                                     │   │
│  │  - /api/v1/tasks           任务管理                     │   │
│  │  - /api/v1/models          模型管理                     │   │
│  │  - /api/v1/skills          技能管理                     │   │
│  │  - /api/v1/intent          意图解析                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  WebSocket                                              │   │
│  │  - /ws/tasks/{task_id}     任务状态实时推送             │   │
│  │  - /ws/broadcast           广播消息                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Intent Parser │    │ Model         │    │ Skill Engine  │
│ 意图解析器    │    │ Dispatcher    │    │ 技能引擎      │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Type System   │    │ Task Engine   │    │ WebSocket     │
│ 类型系统      │    │ 任务执行引擎  │    │ Manager       │
└───────────────┘    └───────┬───────┘    └───────────────┘
                             │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Persistence   │    │ Cache         │    │ Monitoring    │
│ 持久化存储    │    │ 缓存系统      │    │ 监控系统      │
└───────────────┘    └───────────────┘    └───────────────┘
```

## 核心模块

### 1. 意图解析器 (Intent Parser)

**位置**: `src/intent_parser/`

**功能**:
- 解析用户输入，识别意图类型
- 支持多种解析器（本地模型、OpenAI、Claude）
- 提取关键参数和风格信息

**解析器类型**:
- `qwen2.5` - Qwen2.5 本地模型解析器
- `openai` - OpenAI GPT 解析器
- `llama` - Llama 本地模型解析器
- `claude` - Anthropic Claude 解析器

### 2. 模型调度器 (Model Dispatcher)

**位置**: `src/model_dispatcher/`

**功能**:
- 管理已注册的AI模型
- 根据意图选择最佳模型
- 类型兼容性验证

**已注册模型**:
| ID | 类型 | 功能 |
|---|---|---|
| sdxl_1.0 | image | 图片生成 |
| sd_1.5 | image | 图片生成 |
| openai_dall_e | image | 图片生成 |
| stability_ai | image | 图片生成 |
| svd | video | 视频生成 |
| tts | audio | 语音生成 |
| esrgan | upscaler | 图片放大 |
| qwen2.5-7b | text | 文本生成 |
| openai_gpt4 | text | 文本生成 |
| qwen2.5-coder | code | 代码生成 |
| claude_3 | code | 代码生成 |

### 3. 任务执行引擎 (Task Engine)

**位置**: `src/task_engine/`

**功能**:
- 异步任务调度和执行
- 任务状态管理
- 进度追踪和结果存储

**任务类型**:
- `image_generation` - 图片生成
- `video_generation` - 视频生成
- `audio_generation` - 音频生成
- `text_generation` - 文本生成
- `code_generation` - 代码生成
- `image_upscale` - 图片放大
- `image_edit` - 图片编辑
- `skill_execution` - 技能执行

**任务状态**:
- `pending` - 等待执行
- `running` - 执行中
- `completed` - 已完成
- `failed` - 失败
- `cancelled` - 已取消

### 4. 技能引擎 (Skill Engine)

**位置**: `src/skills/`

**功能**:
- 技能加载和管理
- 支持动态和配置两种执行器
- 共享状态管理

**执行器类型**:
- **动态执行器**: Python 代码实现
- **配置执行器**: YAML/JSON 配置定义

**支持的动作**:
- `http_request` - HTTP 请求
- `file_operation` - 文件操作
- `data_transform` - 数据转换
- `shell_command` - Shell 命令

### 5. WebSocket 管理器

**位置**: `src/ws/`

**功能**:
- 实时任务状态推送
- 广播消息
- 心跳检测

**端点**:
- `/ws/tasks/{task_id}` - 任务状态实时推送
- `/ws/broadcast` - 广播消息

### 6. 持久化存储

**位置**: `src/persistence/`

**功能**:
- SQLite 数据库集成
- 任务存储和查询
- 模型使用统计
- 技能管理

**数据表**:
- `tasks` - 任务表
- `model_stats` - 模型统计
- `skills` - 技能表
- `config` - 配置表

### 7. 缓存系统

**位置**: `src/cache/`

**功能**:
- 内存缓存实现
- TTL 过期机制
- LRU 驱逐策略
- 缓存统计

### 8. 监控系统

**位置**: `src/monitoring/`

**功能**:
- 结构化日志记录
- 指标收集
- 健康状态监控

## API 端点

### 任务管理

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/tasks` | POST | 提交任务 |
| `/api/v1/tasks` | GET | 列出任务 |
| `/api/v1/tasks/{task_id}` | GET | 获取任务状态 |
| `/api/v1/tasks/{task_id}` | DELETE | 取消任务 |
| `/api/v1/tasks/statistics` | GET | 任务统计 |

### 模型管理

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/models` | GET | 列出模型 |
| `/api/v1/models/{model_id}` | GET | 获取模型详情 |
| `/api/v1/models/stats` | GET | 模型统计 |

### 技能管理

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/skills` | GET | 列出技能 |
| `/api/v1/skills/{skill_id}` | GET | 获取技能详情 |
| `/api/v1/skills/execute` | POST | 执行技能 |

### 意图解析

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/intent/parse` | POST | 解析意图 |
| `/api/v1/intent/enhance` | POST | 增强提示词 |

## 类型系统

### 意图类型 (IntentType)

```python
IntentType(
    IMAGE_GENERATION = "image_generation",      # 图片生成
    VIDEO_GENERATION = "video_generation",      # 视频生成
    AUDIO_GENERATION = "audio_generation",      # 音频生成
    TEXT_GENERATION = "text_generation",        # 文本生成
    CODE_GENERATION = "code_generation",        # 代码生成
    IMAGE_UPSCALE = "image_upscale",            # 图片放大
    IMAGE_EDIT = "image_edit",                  # 图片编辑
    GENERAL = "general",                        # 通用
)
```

### 模型功能类型 (ModelFunctionType)

```python
ModelFunctionType(
    TEXT_TO_IMAGE = "text_to_image",            # 文本转图片
    TEXT_GENERATION = "text_generation",        # 文本生成
    CODE_GENERATION = "code_generation",        # 代码生成
    TEXT_TO_SPEECH = "text_to_speech",          # 文本转语音
    VIDEO_GENERATION = "video_generation",      # 视频生成
    IMAGE_UPSCALE = "image_upscale",            # 图片放大
    UNKNOWN = "unknown",                        # 未知
)
```

### 模型分类 (ModelCategory)

```python
ModelCategory(
    IMAGE = "image",
    VIDEO = "video",
    AUDIO = "audio",
    TEXT = "text",
    CODE = "code",
    UPSCALER = "upscaler",
)
```

## 配置文件

### 全局配置 (config.yaml)

```yaml
project_root: "/path/to/project"
api:
  host: "0.0.0.0"
  port: 8002
  docs_enabled: true
  cors_origins:
    - "http://localhost:3000"
logging:
  level: "DEBUG"
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
cache:
  max_size: 1000
  default_ttl: 3600
```

### 模型配置 (models.yaml)

```yaml
models:
  - id: "sdxl_1.0"
    name: "SDXL 1.0"
    category: "image"
    function_type: "text_to_image"
    source: "local"
    enabled: true
    config:
      model_path: "./models/sdxl"
```

## 部署方式

### 开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 激活虚拟环境
source .venv/bin/activate

# 运行诊断
python main.py diagnose

# 启动开发服务器
python main.py serve --port 8002
```

### 生产环境

```bash
# 使用 Uvicorn
uvicorn src.api.app:create_app --host 0.0.0.0 --port 8002 --workers 4

# 使用 Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.app:create_app
```

## 测试验证

### 运行诊断

```bash
python main.py diagnose
```

预期输出：
```
=== HydraFlow AI 系统诊断 ===

全局配置: 已加载
模型配置: 已加载
API密钥配置: 已加载

已注册解析器: 4
已加载风格模板: 7
已注册模型: 11
已安装技能: 0

任务执行器: 运行中
缓存管理器: 运行中
监控系统: healthy

系统健康分数: 100.0/100
```

### API 测试

```bash
# 解析意图
curl -X POST http://localhost:8002/api/v1/intent/parse \
  -H "Content-Type: application/json" \
  -d '{"query": "生成一张赛博朋克风格的城市夜景"}'

# 提交任务
curl -X POST http://localhost:8002/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "image_generation",
    "prompt": "赛博朋克城市",
    "model_id": "sdxl_1.0",
    "parameters": {"width": 1024, "height": 768}
  }'

# 获取任务状态
curl http://localhost:8002/api/v1/tasks/{task_id}
```

## 扩展开发

### 添加新技能

1. 创建技能目录：`skills/local/my_skill/`
2. 创建 `manifest.json`
3. 创建 `executor.py` 或 `config.yaml`
4. 通过技能管理器安装

### 添加新模型

1. 在 `models.yaml` 中添加模型配置
2. 实现模型适配器
3. 注册到模型调度器

### 添加新解析器

1. 创建解析器类继承 `IntentParserBase`
2. 实现 `parse` 方法
3. 在 `parser_factory.py` 中注册

## 架构特点

### 优势

1. **模块化设计**: 各模块职责清晰，易于扩展
2. **类型安全**: 完整的类型系统确保兼容性
3. **异步执行**: 支持大规模并发任务
4. **实时推送**: WebSocket 实时状态更新
5. **持久化**: 任务历史和统计数据可追溯
6. **缓存优化**: 减少重复计算

### 未来扩展

1. **分布式任务队列**: 支持多节点部署
2. **模型热加载**: 无需重启即可添加模型
3. **技能市场**: 在线技能商店
4. **用户认证**: OAuth2/JWT 认证
5. **资源管理**: GPU/CPU 资源调度
6. **多租户**: 支持多用户隔离

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-05-01 | 基础功能完成 |
| 1.1.0 | 2026-05-11 | 添加任务引擎、技能引擎、WebSocket |

## 许可证

MIT License

---

**HydraFlow AI - 九头蛇生成式工作流平台** 🐍
