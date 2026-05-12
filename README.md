# HydraFlow AI

**版本**: 2.0.0 | 一个强大的 AI 工作流引擎，支持多模态内容生成、意图解析和技能系统。

---

## 📢 开发声明与邀请

### 关于作者

本人文凭有限，创作这个程序纯属个人爱好，希望各位不要介意使用中碰到的各类问题。想着设计一个基础，也可以开放程序的自由度理念性的改变使用方式和改造。我在努力中，有兴趣的可以加入。

### 开放与自由的理念

HydraFlow AI 从设计之初就秉持**高度自由化**的理念。我们相信：

- **不设限的扩展方式** - 任何人都可以通过插件系统添加自己需要的功能模块
- **理念性改变** - 不仅仅是代码修改，更是鼓励创新的使用场景和工作流
- **社区驱动** - 每个人都可以贡献自己的想法、代码和创意

### 🛠️ 模块添加入口

我们提供了完整的插件系统，让管理员和开发者可以轻松添加自定义模块：

#### 方式一：通过 API 管理插件

```bash
# 列出所有插件
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/plugins

# 加载插件
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/plugins/load/PluginName

# 上传安装插件
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@your-plugin.zip" \
  http://localhost:8000/api/v1/plugins/install/upload
```

#### 方式二：开发自己的插件

1. 在 `plugins/` 目录创建插件文件夹
2. 继承 `BasePlugin` 并实现接口
3. 使用 `@plugin` 装饰器注册
4. 启动服务自动加载

详细开发指南请查看：[插件开发文档](./docs/PLUGIN_DEVELOPMENT.md)

#### 方式三：使用示例插件

项目包含 `plugins/example_hello/` 示例插件，演示如何：
- 添加 API 端点
- 提供 CLI 命令
- 自定义配置
- 声明依赖关系

### 🤝 加入我们

无论您是：
- 🐍 Python 开发者
- 🎨 创意工作者
- 📚 文档编写者
- 💡 有想法的用户

都欢迎加入！您可以：
- 创建 Issue 分享想法
- 提交 Pull Request 贡献代码
- 开发自己的插件模块
- 改进文档和使用体验

让我们一起把这个基础变得更强大！🚀

---

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
