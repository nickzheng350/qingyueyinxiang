# 📚 HydraFlow AI 文档中心

> **版本**: v1.1.0
> **最后更新**: 2026-04-18

---

## 📖 文档导航

### 核心文档

| 文档 | 说明 |
|------|------|
| [00-快速开始指南.md](./00-快速开始指南.md) | 3步快速上手，新用户必读 |
| **[完整使用指南.md](./完整使用指南.md)** | 综合使用手册，涵盖所有功能 |

---

## 🎯 新手指南

如果你是第一次使用 HydraFlow AI：

1. **[00-快速开始指南.md](./00-快速开始指南.md)** - 3步快速上手
2. **[完整使用指南.md](./完整使用指南.md)** - 完整功能说明

---

## 🛠️ 主要功能

### 技能系统

- 支持 **5大技能市场**：
  - Hugging Face (https://huggingface.co)
  - ModelScope (https://www.modelscope.cn)
  - GitHub (https://github.com)
  - LangChain (https://smith.langchain.com)
  - HydraFlow 官方 (https://hydraflow-ai.org)

- **精选技能**：
  - 图像生成：Stable Diffusion XL, ControlNet, SDXL Turbo
  - 大语言模型：Llama 3, Qwen2.5, ChatGLM3, InternLM2
  - 语音处理：Whisper Large V3
  - 开发框架：LangChain, AutoGen, llama.cpp

详细说明请查看 **[完整使用指南.md](./完整使用指南.md)**

---

## 📊 精选技能列表

| 类别 | 技能 | 来源 | 下载量 | 评分 |
|------|------|------|--------|------|
| 🎨 图像 | Stable Diffusion XL | Hugging Face | 523,456 | ⭐4.9 |
| 🎨 图像 | ControlNet | Hugging Face | 456,789 | ⭐4.9 |
| 🦙 语言 | Llama 3 8B | Hugging Face | 345,678 | ⭐4.8 |
| 🔮 语言 | Qwen2.5 7B | ModelScope | 234,567 | ⭐4.8 |
| 🎤 语音 | Whisper Large V3 | Hugging Face | 189,234 | ⭐4.9 |
| 🔗 框架 | LangChain | GitHub | 789,012 | ⭐4.8 |

---

## 🔗 快速链接

### 官方资源

- **GitHub**: https://github.com/HydraFlowAI/HydraFlow_AI
- **Issues**: https://github.com/HydraFlowAI/HydraFlow_AI/issues

### 技能市场

- **Hugging Face**: https://huggingface.co/models
- **ModelScope**: https://www.modelscope.cn/models
- **GitHub**: https://github.com

---

## 💡 使用技巧

### 安装技能

```bash
# 搜索技能
python scripts/skill_installer.py search "stable diffusion"

# 从市场安装
python scripts/skill_installer.py install-market hf_stable_diffusion_xl

# 从本地安装
python scripts/skill_installer.py install-path /path/to/skill
```

### Python API

```python
from src.skills.skill_manager import SkillManager

manager = SkillManager()

# 搜索市场
skills = manager.search_market_skills(query="coding", limit=10)

# 安装技能
result = manager.install_skill_from_market("hf_llama3_8b")
```

---

**更新日期**: 2026-04-18

**Happy Generating! 🎨✨**
