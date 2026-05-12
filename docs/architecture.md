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

### 生成类一致性验证 (Generation Consistency Validation)

系统提供完整的生成类一致性验证机制，包括：

**验证规则类型 (ValidationRuleType)**:
- `input_format` - 输入格式验证
- `output_format` - 输出格式验证
- `resource_constraint` - 资源约束验证
- `quality_standard` - 质量标准验证
- `safety_check` - 安全检查
- `performance_bound` - 性能边界验证
- `compatibility` - 兼容性验证

**验证触点 (TouchPoint)**:
- `pre_processing` - 预处理阶段
- `model_input` - 模型输入
- `model_execution` - 模型执行
- `model_output` - 模型输出
- `post_processing` - 后处理阶段
- `result_delivery` - 结果交付

**边界类型 (BoundaryType)**:
- `hard_boundary` - 硬边界：违反则任务失败
- `soft_boundary` - 软边界：违反可继续但有警告
- `advisory_boundary` - 建议边界：最佳实践提示

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
    TEXT_TO_VIDEO = "text_to_video",            # 文本转视频
    TEXT_TO_AUDIO = "text_to_audio",            # 文本转音频
    TEXT_GENERATION = "text_generation",        # 文本生成
    CODE_GENERATION = "code_generation",        # 代码生成
    IMAGE_UPSCALE = "image_upscale",            # 图片放大
    IMAGE_EDIT = "image_edit",                  # 图片编辑
    IMAGE_TO_VIDEO = "image_to_video",          # 图生视频
    IMAGE_STYLE_TRANSFER = "image_style_transfer",  # 图片风格转换
    IMAGE_FORMAT_CONVERT = "image_format_convert",  # 图片格式转换
    VIDEO_STYLE_TRANSFER = "video_style_transfer",  # 视频风格转换
    VIDEO_FORMAT_CONVERT = "video_format_convert",  # 视频格式转换
    AUDIO_STYLE_TRANSFER = "audio_style_transfer",  # 音频风格转换
    AUDIO_FORMAT_CONVERT = "audio_format_convert",  # 音频格式转换
    IMAGE_TO_AUDIO = "image_to_audio",          # 图生音频
    AUDIO_TO_TEXT = "audio_to_text",            # 语音转文本
    VIDEO_TO_AUDIO = "video_to_audio",          # 视频转音频
    VIDEO_TO_TEXT = "video_to_text",            # 视频转文本
    IMAGE_TO_TEXT = "image_to_text",            # 图片转文本
    TEXT_TO_3D = "text_to_3d",                  # 文本转3D
    IMAGE_TO_3D = "image_to_3d",                # 图片转3D
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

## 多模态模块 (Multimodal Modules)

### 图生视频 (Image-to-Video)

**位置**: `src/multimodal/image_to_video.py`

**功能**:
- 将静态图片转换为动态视频
- 支持多种运动类型：
  - `camera_pan` - 镜头平移
  - `camera_zoom` - 镜头缩放
  - `camera_tilt` - 镜头倾斜
  - `subject_motion` - 主体运动
  - `particle_effect` - 粒子特效
- 可配置视频时长、帧率、分辨率等
- 一致性验证集成

**使用示例**:
```python
from src.multimodal import ImageToVideoGenerator
from src.multimodal.image_to_video import ImageToVideoConfig, VideoMotionType

generator = ImageToVideoGenerator()
config = ImageToVideoConfig(
    duration=5.0,
    fps=24,
    motion_type=VideoMotionType.CAMERA_PAN,
    motion_strength=0.5,
)
result = generator.generate("input.jpg", config)
```

### 风格转换 (Style Transfer)

**位置**: `src/multimodal/style_transfer.py`

**功能**:
- 图片风格转换（支持多种艺术风格）
- 视频风格转换
- 音频风格转换
- 预设风格库：
  - Van Gogh、Picasso、Monet、Da Vinci
  - Anime、Cyberpunk、Watercolor、Oil Painting
  - Classical、Jazz、Rock、Pop等音频风格

**使用示例**:
```python
from src.multimodal import StyleTransferEngine
from src.multimodal.style_transfer import StyleTransferConfig, ArtStyle

engine = StyleTransferEngine()
config = StyleTransferConfig(
    style=ArtStyle.VAN_GOGH,
    style_strength=0.7,
)
result = engine.transfer_image_style("input.jpg", config)
```

### 格式转换 (Format Converter)

**位置**: `src/multimodal/format_converter.py`

**功能**:
- 图片格式转换 (PNG, JPG, WebP, GIF等)
- 视频格式转换 (MP4, AVI, MOV, MKV等)
- 音频格式转换 (WAV, MP3, FLAC, AAC等)
- 支持质量、分辨率、码率等参数调整
- 内置一致性验证

**使用示例**:
```python
from src.multimodal import FormatConverter
from src.multimodal.format_converter import ImageFormatConfig

converter = FormatConverter()
config = ImageFormatConfig(
    output_format="webp",
    quality=90,
    optimize=True,
)
result = converter.convert_image("input.png", config)
```

### 音频提示词数字公式化引擎 (Audio Prompt Engine)

**位置**: `src/multimodal/audio_prompt_engine.py`

**功能**:
- 自然语言提示词解析为数字参数
- 15维风格参数向量：
  - 时域：tempo, rhythm_complexity, dynamics_range
  - 频域：brightness, warmth, harmonic_richness
  - 情感：emotional_tone, energy_level, valence, arousal
  - 空间：reverb_level, stereo_width
  - 人声：pitch_shift, vibrato_depth
  - 流派：genre_influence
- 风格预设库（12种流派）
- 参数组合优化和变体生成
- 风格混合功能

**使用示例**:
```python
from src.multimodal import AudioPromptEngine
from src.multimodal.audio_prompt_engine import MusicalGenre

engine = AudioPromptEngine()
result = engine.optimize_prompt(
    "a calm, relaxing piece of music",
    target_genre=MusicalGenre.LO_FI,
    num_variations=3,
)

params = result.style_params
vector = params.to_numeric_vector()
```

## 增强音频引擎 (Enhanced Audio Engine)

**位置**: `src/multimodal/enhanced_audio_engine.py`

**功能**:
- 剧本解析 - 识别场景、角色、对话
- 风格统一性配音 - 基于项目风格指南确保一致性
- 角色配置管理 - 音高、语速、音色等参数化
- 场景风格生成 - 根据场景类型自动生成音频风格
- 配音计划创建 - 时间、情感、角色的完整配音计划

**核心组件**:
- `ScriptParser` - 剧本解析器
- `StyleConsistencyEngine` - 风格一致性引擎
- `AVFusionEngine` - 音视频融合引擎
- `EnhancedAudioEngine` - 增强音频引擎（整合入口）

**使用示例**:
```python
from src.multimodal import EnhancedAudioEngine, ProjectStyleGuide
from src.multimodal.audio_prompt_engine import MusicalGenre

style_guide = ProjectStyleGuide(
    project_id="my_film",
    genre=MusicalGenre.CINEMATIC,
    overall_mood="dramatic",
    target_era="contemporary",
    base_tempo_range=(70.0, 130.0),
    base_dynamics=0.6,
    reverb_character="large_hall",
    orchestration_style="hybrid",
    mixing_balance={"voice": 0.6, "music": 0.3, "sfxs": 0.1}
)

engine = EnhancedAudioEngine()
script = """
SCENE 1: INT. LIVING ROOM - DAY
ALICE: Hello, how are you today?
BOB: I'm doing great, thanks for asking!
"""
parse_result, plans = engine.process_script(script, style_guide)
```

## 音视频多模态融合引擎 (AV Multimodal Fusion)

**位置**: `src/multimodal/av_multimodal_fusion.py`

**功能**:
- 电影级音视频融合 - 支持多轨道、混音、同步
- 独立生成能力 - 音频和视频可分别独立生成
- 制作质量等级 - Web、广播、电影、杜比视界、IMAX
- 项目资产管理 - 时间线、轨道、资产库
- 工作流自动化 - 自动构建和执行制作流程

**核心组件**:
- `AVMultimodalFusionEngine` - 融合引擎主入口
- `WorkflowEngine` - 工作流引擎
- `Project` - 项目数据结构
- `ProductionSettings` - 制作设置

**质量等级**:
- `WEB` - 网络流媒体
- `BROADCAST` - 广播电视
- `CINEMATIC` - 电影级
- `DOLBY_VISION` - 杜比视界
- `IMAX` - IMAX级别

**使用示例**:
```python
from src.multimodal import AVMultimodalFusionEngine, ProductionSettings, ProductionQuality

engine = AVMultimodalFusionEngine()

settings = ProductionSettings(
    quality=ProductionQuality.CINEMATIC,
    resolution=(1920, 1080),
    fps=24.0,
    bitrate_video="20M"
)

project = engine.create_project(
    project_name="My Film",
    style_guide=style_guide,
    settings=settings
)

# 独立生成音频
audio_asset = engine.generate_independent_audio(
    project, "Ambient background music", MusicalGenre.CINEMATIC
)

# 独立生成视频
video_asset = engine.generate_independent_video(
    project, "reference.jpg", video_config
)

# 电影级融合
result = engine.fuse_cinematic(project)
```

## 工作流整合模块 (Workflow Integration)

**位置**: `src/multimodal/workflow_integration.py`

**功能**:
- 项目模板库 - 预设类型（短片、播客、音乐视频等）
- 批量处理 - 同类型项目统一整合
- 工作流策略 - 顺序、并行、流水线、模块化
- 项目合并 - 多个项目整合为一个
- 统一管理 - 一键启动、完整制作、状态跟踪

**项目模板**:
- `short_film` - 短片模板（电影级质量）
- `podcast` - 播客模板（广播级质量）
- `music_video` - 音乐视频模板（高质量）

**整合策略**:
- `SEQUENTIAL` - 顺序处理
- `PARALLEL` - 并行处理
- `PIPELINE` - 流水线
- `MODULAR` - 模块化

**使用示例**:
```python
from src.multimodal import UnifiedProjectManager, ProjectType

manager = UnifiedProjectManager()

# 快速启动项目
project = manager.quick_start(
    ProjectType.SHORT_FILM,
    "My Short Film",
    script_text
)

# 完整制作流程
result = manager.complete_production(project)

# 批量处理多个项目
projects = [project1, project2, project3]
batch_config = BatchConfig(batch_id="batch_001", strategy=IntegrationStrategy.PIPELINE)
batch_result = manager.integrator.batch_process_projects(projects, batch_config)
```

## 统一智能引擎 (Unified Intelligent Engine)

**位置**: `src/core/unified_engine.py`

**功能**:
- 唯一引擎入口 - 单一入口整合所有模块
- 智能调度 - 优先级队列，组合式调度
- 资源优化 - 成本节约，效能增长
- 多模态配合 - 音频、视频、图像、文本协同
- 性能监控 - 实时指标，告警机制

**核心组件**:
- `UnifiedIntelligentEngine` - 统一智能引擎（单例模式）
- `SmartScheduler` - 智能调度器
- `ResourceOptimizer` - 资源优化器
- 子引擎: `AudioSubEngine`, `VideoSubEngine`, `VisualSubEngine`, `TextSubEngine`, `FusionSubEngine`

**引擎模式**:
- `EFFICIENCY` - 效率优先
- `QUALITY` - 质量优先
- `BALANCED` - 平衡模式
- `ECO` - 节能模式

**使用示例**:
```python
from src.core import get_unified_engine, EngineMode, TaskPriority, ModelFunctionType

# 获取统一引擎（单例）
engine = get_unified_engine()

# 启动引擎
engine.start()

# 设置模式
engine.set_engine_mode(EngineMode.BALANCED)

# 创建多元化提示词
prompt = engine.create_prompt("A beautiful sunset over mountains")

# 提交任务
task_id = engine.submit_task(
    ModelFunctionType.TEXT_TO_IMAGE,
    prompt,
    priority=TaskPriority.HIGH,
)

# 获取结果
result = engine.get_task_result(task_id)

# 查看性能指标
metrics = engine.get_performance_metrics()

# 停止引擎
engine.stop()
```

## 多元化提示词引擎 (Diversified Prompt Engine)

**位置**: `src/core/prompt_engine.py`

**功能**:
- 结构完整 - 多元素，多角色，多配置
- 跨类型互补 - 自动建议互补任务
- 质量等级 - FAST, STANDARD, HIGH, ULTRA
- 智能构建 - 文本、图像、音频、视频专用构建器

**核心组件**:
- `DiversifiedPromptEngine` - 多元化提示词引擎
- `PromptBuilder` - 提示词构建器
- `CrossTypeComplementEngine` - 跨类型互补引擎
- `PromptOptimizer` - 提示词优化器

**提示词角色**:
- `PRIMARY` - 主要内容
- `SECONDARY` - 次要内容
- `SUPPORT` - 支持内容
- `CONSTRAINT` - 约束条件
- `STYLE` - 风格提示
- `NEGATIVE` - 负面提示

**使用示例**:
```python
from src.core import DiversifiedPromptEngine, PromptType, QualityLevel, AspectRatio

prompt_engine = DiversifiedPromptEngine()

# 构建图像提示词
image_prompt = prompt_engine.create_prompt(
    PromptType.IMAGE,
    "A cyberpunk city at night with neon lights",
    style="Blade Runner 2049",
    aspect_ratio=AspectRatio.WIDE,
    quality=QualityLevel.HIGH,
    negatives=["blurry", "low quality"],
)

# 获取互补建议
suggestions = prompt_engine.get_complementary_suggestions(image_prompt)
for suggestion in suggestions:
    print(f"Suggest: {suggestion['type']} (Relevance: {suggestion['relevance']})")

# 构建组合提示词
combined_prompt = prompt_engine.builder.build_combined_prompt([image_prompt, audio_prompt])

# 导出为JSON
prompt_json = combined_prompt.to_json()
```

## 性能监控与优化 (Performance Monitor & Optimizer)

**位置**: `src/core/performance.py`

**功能**:
- 实时监控 - CPU、内存、GPU使用率
- 告警机制 - 多级告警，回调通知
- 成本追踪 - 任务成本，节约估算
- 自适应优化 - 自动调整，策略切换
- 历史记录 - 优化动作历史

**核心组件**:
- `UnifiedPerformanceManager` - 统一性能管理器
- `PerformanceMonitor` - 性能监控器
- `CostTracker` - 成本追踪器
- `PerformanceOptimizer` - 性能优化器

**优化策略**:
- `LATENCY` - 延迟优先（低并发，高缓存）
- `THROUGHPUT` - 吞吐量优先（高并发，批处理）
- `COST` - 成本优先（节能模式）
- `BALANCED` - 平衡模式

**使用示例**:
```python
from src.core import UnifiedPerformanceManager, OptimizationStrategy

perf_manager = UnifiedPerformanceManager()

# 启动监控
perf_manager.start()

# 设置优化策略
perf_manager.set_optimization_strategy(OptimizationStrategy.THROUGHPUT)

# 记录任务成本
perf_manager.record_task(
    task_id="task_001",
    task_type="text_to_image",
    cost=1.5,
    optimized=True,
)

# 查看系统状态
status = perf_manager.get_status()
print(f"CPU: {status['performance']['cpu']}%")
print(f"Memory: {status['performance']['memory']}%")
print(f"Total cost: ${status['cost']['total_cost']}")
print(f"Savings: ${status['cost']['estimated_savings']}")

# 停止监控
perf_manager.stop()
```

## 完整工作流示例

```python
from src.core import (
    get_unified_engine,
    DiversifiedPromptEngine,
    UnifiedPerformanceManager,
    EngineMode,
    OptimizationStrategy,
    ModelFunctionType,
    TaskPriority,
    PromptType,
    QualityLevel,
)

# 1. 初始化所有系统
unified_engine = get_unified_engine()
prompt_engine = DiversifiedPromptEngine()
perf_manager = UnifiedPerformanceManager()

# 2. 配置
unified_engine.set_engine_mode(EngineMode.BALANCED)
perf_manager.set_optimization_strategy(OptimizationStrategy.BALANCED)

# 3. 启动
unified_engine.start()
perf_manager.start()

# 4. 创建多元化提示词
image_prompt = prompt_engine.create_prompt(
    PromptType.IMAGE,
    "A majestic lion on a cliff",
    quality=QualityLevel.HIGH,
)

# 5. 提交任务
task_id = unified_engine.submit_task(
    ModelFunctionType.TEXT_TO_IMAGE,
    image_prompt,
    priority=TaskPriority.MEDIUM,
)

# 6. 获取互补建议并添加更多任务
suggestions = prompt_engine.get_complementary_suggestions(image_prompt)
for suggestion in suggestions[:2]:
    unified_engine.submit_task(
        suggestion["type"],
        image_prompt,
        priority=TaskPriority.LOW,
    )

# 7. 获取结果
result = unified_engine.get_task_result(task_id)

# 8. 监控性能
status = perf_manager.get_status()
print(f"System status: {status}")

# 9. 清理
perf_manager.stop()
unified_engine.stop()
```

## 提示词敏锐性引擎

**位置**: `src/core/prompt_awareness.py`

**功能**:
- 关键词分析 - 提取、优先级、频率分析
- 意图检测 - 识别创意、技术、质量等意图
- 质量评估 - 清晰度、具体性、结构评分
- 提示词画像 - 内容类别、复杂度、风格分析
- 增强建议 - 自动生成改进建议
- 引擎推荐 - 根据分析结果推荐最佳引擎

**核心组件**:
- `PromptAwarenessEngine` - 统一敏锐性引擎入口
- `PromptAnalyzer` - 提示词分析器
- `PromptEnhancer` - 提示词增强器
- `MultimodalRouter` - 多模态路由器

**使用示例**:
```python
from src.core import (
    PromptAwarenessEngine,
    DiversifiedPromptEngine,
    PromptType,
    QualityLevel,
)

prompt_engine = DiversifiedPromptEngine()
awareness_engine = PromptAwarenessEngine()

# 创建提示词
prompt = prompt_engine.create_prompt(
    PromptType.IMAGE,
    "A beautiful sunset over mountains in the style of Van Gogh, masterpiece, best quality, 8k",
    quality=QualityLevel.HIGH,
)

# 完整分析
analysis = awareness_engine.analyze(prompt)

print(f"主要意图: {analysis.intent_detection.primary_intent}")
print(f"整体质量: {analysis.quality_assessment.overall_quality}")
print(f"推荐引擎: {analysis.recommended_engines}")

# 查看增强建议
for suggestion in analysis.enhancement_suggestions:
    print(f"建议: {suggestion.description}")
```

## 完整工作流路线 - 提示词--多维引擎--运行--输出

**位置**: `src/core/workflow_orchestrator.py`

**工作流阶段**:
1. **INPUT (输入)** - 接收原始提示词
2. **AWARENESS (敏锐性分析)** - 分析、画像、意图识别
3. **ENHANCEMENT (增强)** - 提示词优化、增强
4. **ROUTING (路由)** - 选择最佳引擎
5. **EXECUTION (执行)** - 引擎处理
6. **VALIDATION (验证)** - 一致性验证
7. **OUTPUT (输出)** - 结果返回

**核心组件**:
- `WorkflowOrchestrator` - 工作流编排器（单例模式）
- `WorkflowStageProcessor` - 阶段处理器
- 支持 AUTO/GUIDED/MANUAL/CUSTOM 模式

**使用示例**:
```python
from src.core import (
    get_workflow_orchestrator,
    PromptType,
    QualityLevel,
    TaskPriority,
)

# 获取编排器
orchestrator = get_workflow_orchestrator()

# 启动服务
orchestrator.start_services()

# 快速处理 - 一键完整路线
result = orchestrator.quick_process(
    "A majestic lion on a cliff at sunset, masterpiece, best quality, 8k",
    prompt_type=PromptType.IMAGE,
    quality=QualityLevel.HIGH,
    priority=TaskPriority.HIGH,
)

print(f"成功: {result.success}")
print(f"输出: {result.output}")

# 查看敏锐性分析
if result.awareness_result:
    print(f"意图: {result.awareness_result.intent_detection.primary_intent}")
    print(f"质量: {result.awareness_result.quality_assessment.overall_quality}")

# 分步骤执行 - 可干预模式
execution_id = orchestrator.create_workflow(
    "Cyberpunk city at night",
    prompt_type=PromptType.IMAGE,
)
result = orchestrator.execute_workflow(execution_id)

# 查看系统总结
summary = orchestrator.get_system_summary()
print(f"总执行: {summary['total_executions']}")

# 停止服务
orchestrator.stop_services()
```

## 系统集成 - 提示词与全功能系统

**提示词参与的完整系统**:
```
┌─────────────────────────────────────────────────────────────┐
│                        输入层                                │
│              简单字符串 / RichPrompt                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              提示词敏锐性引擎                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 关键词分析  │ │ 意图检测    │ │ 质量评估    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 提示词画像  │ │ 增强建议    │ │ 引擎推荐    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                 工作流编排器                                 │
│      ┌─────────────────────────────────────────┐          │
│      │ 阶段处理器: INPUT → AWARENESS →        │          │
│      │          ENHANCEMENT → ROUTING →       │          │
│      │          EXECUTION → VALIDATION →      │          │
│      │          OUTPUT → COMPLETED            │          │
│      └─────────────────────────────────────────┘          │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    多维引擎层                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 音频引擎    │ │ 视频引擎    │ │ 视觉引擎    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐                         │
│  │ 文本引擎    │ │ 融合引擎    │                         │
│  └──────────────┘ └──────────────┘                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                 运行与优化层                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 性能监控    │ │ 成本跟踪    │ │ 资源优化    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐                         │
│  │ 多级缓存    │ │ 并发管理    │                         │
│  └──────────────┘ └──────────────┘                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      输出层                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 图片输出    │ │ 音频输出    │ │ 视频输出    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐                         │
│  │ 文本输出    │ │ 元数据      │                         │
│  └──────────────┘ └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

**全系统功能覆盖**:
1. 文本→音频（含剧本解析）
2. 文本→图像（含风格转换）
3. 文本→视频（含音频驱动）
4. 图像→视频（含音视频融合）
5. 音频→视频（含声音设计）
6. 音视频融合（电影级）
7. 所有功能的质量一致性验证
8. 所有阶段的性能监控与优化

## 完整提示词库 - 细粒度分类

**位置**: `src/core/prompt_library.py`

**核心分类 (8大类)**:
1. **风格 (STYLE)** - 绘画、动漫、摄影、特殊风格
2. **内容 (CONTENT)** - 场景、人物、物体、特殊内容
3. **质量 (QUALITY)** - 基础质量、细节、专业度、分辨率
4. **光线 (LIGHTING)** - 光源类型、光效、氛围光
5. **氛围 (ATMOSPHERE)** - 情感、戏剧、宁静、紧张等
6. **相机 (CAMERA)** - 视角、镜头类型、技术参数
7. **色彩 (COLOR)** - 色彩方案、对比、分级
8. **艺术家 (ARTIST)** - 具体艺术家风格

**细粒度分类**:
```
风格类 (FineStyle):
├── 绘画风格: 印象派、超现实主义、立体主义、抽象、现实主义、波普、装饰艺术
├── 动漫风格: 漫画、动漫、吉卜力、新海诚
├── 现代风格: 赛博朋克、蒸汽朋克、柴油朋克、太阳朋克
├── 摄影风格: 写实、人像、风景、街拍、艺术摄影
└── 特殊风格: 水彩、油画、国画、像素、矢量、3D渲染

内容类 (FineContent):
├── 场景: 城市、自然、风景、海景、山景、森林、沙漠、海洋
├── 人物: 人类、肖像、奇幻、超级英雄、动漫角色
├── 物体: 交通工具、动物、建筑、家具、食物
└── 特殊: 抽象图案、文字、标志

质量类 (FineQuality):
├── 基础质量: 低、标准、高、超高质量、杰作
├── 质量细节: 高细节、超高细节、清晰、锐利、对焦准确
├── 专业质量: 专业、获奖、艺术画廊、博物馆级
└── 分辨率: HD、Full HD、2K、4K、8K、16K

光线类 (FineLighting):
├── 光源: 自然光、阳光、月光、人造光、黄金小时、蓝调时刻、日出、日落
├── 光效: 柔光、硬光、轮廓光、背光、主光、补光、霓虹、生物发光
└── 氛围光: 戏剧化、情绪、神秘、温暖、凉爽、电影感

氛围类 (FineAtmosphere):
├── 情感类: 情绪化、戏剧化、宁静、紧张、快乐、忧郁、兴奋、神秘、魔法、恐怖、温馨、活力

相机类 (FineCamera):
├── 视角: 特写、中景、广角、超广角、航拍、鸟瞰、虫眼
├── 镜头: 长焦、鱼眼、广角、微距
└── 参数: 散景、浅景深、长曝光、低快门、高快门、光圈值

色彩类 (FineColor):
├── 色彩方案: 鲜艳、柔和、低饱和、温暖、凉爽、单色、黑白、高对比、低对比、色彩分级
```

**核心组件**:
- `PromptLibrary` - 完整提示词库（统一入口）
- `StyleLibrary` - 风格库
- `ContentLibrary` - 内容库
- `QualityLibrary` - 质量库
- `LightingLibrary` - 光线库
- `PromptTemplate` - 提示词模板
- `PromptComponent` - 可组合的提示词组件

**使用示例**:
```python
from src.core import (
    get_prompt_library,
    get_multi_dimensional_engine,
    FineStyle,
    FineContent,
    FineQuality,
    FineLighting,
)

# 获取提示词库
prompt_lib = get_prompt_library()

# 方式1: 使用模板构建
prompt = prompt_lib.build_prompt(
    template_id="art_creation",
    content="A beautiful sunset over mountains",
    style=FineStyle.CYBERPUNK,
    quality=FineQuality.MASTERPIECE,
    lighting=FineLighting.GOLDEN_HOUR,
)

# 方式2: 获取特定库的提示词
style_prompts = prompt_lib.style_lib.get(FineStyle.STUDIO_GHIBLI)
quality_prompts = prompt_lib.quality_lib.get(FineQuality.EIGHT_K)

# 获取多维引擎
md_engine = get_multi_dimensional_engine()

# 使用多维引擎生成
result = md_engine.generate_with_dimensions(
    content="A futuristic cityscape",
    style=FineStyle.CYBERPUNK,
    quality=FineQuality.MASTERPIECE,
    lighting=FineLighting.NEON,
)

print(f"生成的提示词: {result['prompt']}")
print(f"使用的维度: {result['dimensions']}")

# 获取所有可用维度
available_dims = md_engine.get_available_dimensions()
print(f"可用风格: {available_dims['styles']}")
print(f"可用内容: {available_dims['contents']}")
```

## 多维引擎 - 维度完整

**位置**: `src/core/prompt_library.py`

**完整维度 (9维)**:
1. **Style (风格)** - 艺术风格、摄影风格、动漫风格等
2. **Content (内容)** - 场景、人物、物体
3. **Quality (质量)** - 质量等级、细节、分辨率
4. **Lighting (光线)** - 光源、光效、氛围光
5. **Atmosphere (氛围)** - 情感氛围
6. **Camera (相机)** - 视角、镜头、技术参数
7. **Color (色彩)** - 色彩方案
8. **Artist (艺术家)** - 艺术家风格
9. **Composition (构图)** - 构图设置

**维度参数化**:
每个维度支持细粒度的枚举类型，可精确控制提示词生成。

**核心组件**:
- `MultiDimensionalEngine` - 多维引擎
- 9个维度的枚举类型定义
- 维度参数化配置
- 提示词构建与组合系统

**使用示例**:
```python
from src.core import get_multi_dimensional_engine, FineStyle, FineQuality, FineLighting

# 获取多维引擎
engine = get_multi_dimensional_engine()

# 完整维度生成
result = engine.generate_with_dimensions(
    content="A dragon flying over a mountain castle",
    style=FineStyle.FANTASY,
    quality=FineQuality.MASTERPIECE,
    lighting=FineLighting.DRAMATIC,
    # 可扩展的维度
)

print(f"提示词: {result['prompt']}")
print(f"维度配置: {result['dimensions']}")

# 查看所有可用维度
dims = engine.get_available_dimensions()
print(f"可用风格数: {len(dims['styles'])}")
print(f"可用光线: {dims['lightings']}")
```

**预设模板**:
1. **art_creation** - 通用艺术创作
2. **portrait_photography** - 专业人像摄影
3. **cyberpunk** - 赛博朋克场景
4. （可扩展自定义）

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
