# 🐍 HydraFlow AI

**九头蛇生成式工作流平台** — 集成意图解析、模型调度、技能管理和工作流引擎的 AI 生成式工作流平台。

## ✨ 特性

- 🎨 **多风格图像生成** — 赛博朋克、动漫、奇幻、照片级真实感等 7 种风格模板
- 🤖 **多解析器支持** — Qwen2.5、Llama (本地) + OpenAI、Claude (API)
- 📦 **技能系统** — 可扩展的技能市场，支持本地安装和市场安装
- 🔧 **CLI 工具** — 一键安装、环境检查、服务启动
- 🌐 **Web UI** — 现代化暗色主题界面
- ⚡ **FastAPI 后端** — 高性能异步 API 服务

## 🚀 快速开始

### 前置要求

- **Node.js**: 16.0+
- **Python**: 3.10 - 3.13

### 安装

```bash
# 克隆项目
git clone https://github.com/HydraFlowAI/HydraFlow_AI.git
cd HydraFlow_AI

# 安装 Node.js 依赖
npm install

# 全局链接（可选）
npm link

# 一键安装所有依赖
hydraflow install
```

### 启动

```bash
# 终端 1 - 启动 API
hydraflow api

# 终端 2 - 启动 UI
hydraflow ui
```

访问地址:
- API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- Web UI: http://localhost:3000

## 📋 命令列表

| 命令 | 说明 |
|------|------|
| `hydraflow install` | 一键安装所有依赖 |
| `hydraflow check` | 检查环境和依赖 |
| `hydraflow api` | 启动 API 服务 |
| `hydraflow ui` | 启动 UI 服务 |
| `hydraflow dev` | 开发模式 |
| `hydraflow install-python` | 安装 Python 依赖 |
| `hydraflow install-deps` | 安装所有依赖 |

## 🏗️ 项目结构

```
HydraFlow_AI/
├── bin/                # CLI 工具
│   └── hydraflow.js    # CLI 入口
├── lib/                # Node.js 核心库
├── src/                # Python 源代码
│   ├── core/          # 核心框架（配置、稳定性、异常）
│   ├── intent_parser/ # 意图解析
│   ├── model_dispatcher/ # 模型调度
│   ├── prompt_engine/ # 提示词引擎
│   ├── api/           # FastAPI 服务
│   └── skills/        # 技能管理
├── ui/                 # Web UI
├── skills/             # 技能库
├── config/             # 配置文件
├── prompts/            # 提示词模板
├── scripts/            # 安装脚本
├── docs/               # 文档
├── main.py            # Python 入口
└── package.json        # Node.js 配置
```

## 📖 文档

- [快速开始指南](docs/00-快速开始指南.md)
- [完整使用指南](docs/完整使用指南.md)

## 📄 许可证

[MIT License](LICENSE)
