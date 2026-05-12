# HydraFlow AI

**版本**: 2.0.0 | 一个强大的 AI 工作流引擎，支持多模态内容生成、意图解析和技能系统。

## 功能特性

- **智能意图解析** - 基于关键词优先和 LLM 辅助的混合解析策略
- **多模态支持** - 支持图像生成、视频生成、代码生成等多种模态
- **技能系统** - 可扩展的技能插件架构
- **性能优化** - 智能缓存、复杂度分析、减少对模型的绝对依赖
- **跨平台** - 支持 Linux、macOS 和 Windows

## 新版本特性 (v2.0)

| 特性 | 说明 |
|------|------|
| 多级缓存优先队列 | L1 LRU + L2 优先级队列，支持 TTL 过期 |
| 统一并发框架 | 同步/异步/并行三种执行模式自动切换 |
| OpenTelemetry 追踪 | 全链路追踪支持，Span 上下文传播 |
| 全局异常处理 | 标准化错误响应，请求 ID 追踪 |
| 轻量级 RAG | 本地/远程嵌入模型，向量检索增强 |
| 100% 类型安全 | 完整类型提示覆盖 |

## 快速开始

### 环境要求

- Python 3.10+
- Git
- 推荐 8GB+ RAM，支持 CUDA 的 GPU（可选）

### 一键安装

**Linux / macOS:**
```bash
git clone https://github.com/yourusername/hydraflow-ai.git
cd hydraflow-ai
chmod +x install.sh
./install.sh
```

**Windows:**
```cmd
git clone https://github.com/yourusername/hydraflow-ai.git
cd hydraflow-ai
install.bat
```

### 手动安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/hydraflow-ai.git
cd hydraflow-ai

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env

# 运行诊断
python main.py diagnose

# 启动服务
python main.py
```

## 配置说明

### 意图解析配置

```json
{
  "intent_parser": {
    "use_llm": true,
    "llm_threshold": "medium",
    "enable_cache": true,
    "cache_ttl": 3600
  }
}
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| use_llm | 是否启用 LLM 辅助解析 | true |
| llm_threshold | LLM 触发阈值 | medium |
| enable_cache | 启用结果缓存 | true |
| cache_ttl | 缓存有效期（秒） | 3600 |

## API 使用

### 解析意图

```bash
curl -X POST http://localhost:8000/api/v1/intent/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "生成一张赛博朋克风格的图片"}'
```

### 生成内容

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "生成一张猫的图片"}'
```

## 项目结构

```
hydraflow-ai/
├── src/              # 核心源代码
│   ├── api/          # API 路由
│   ├── intent_parser/ # 意图解析模块
│   ├── model_dispatcher/ # 模型调度器
│   ├── prompt_engine/   # 提示词引擎
│   ├── skills/        # 技能系统
│   ├── cache/         # 多级缓存优先队列
│   ├── core/          # 核心模块（并发、异常）
│   ├── monitoring/    # 监控追踪
│   └── rag/           # RAG 系统
├── config/           # 配置文件
├── docs/             # 文档
├── prompts/          # 提示词模板
└── skills/           # 技能插件
```

## 性能优化

1. **关键词优先解析** - 简单查询跳过 LLM，响应时间提升 1000 倍
2. **智能缓存** - 重复查询直接返回缓存结果
3. **复杂度分析** - 根据查询复杂度动态选择解析策略
4. **内存优化** - 模型按需加载，减少显存占用
5. **多级缓存** - L1 LRU + L2 优先级队列，命中率提升
6. **并发执行** - 统一执行框架，自动选择最优模式

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
