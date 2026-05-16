# 品牌更名变更日志

> 项目名称：**HydraFlow** → **清悦印象**
> 更名日期：2026-01-20
> 版本：2.0.0

---

## 一、变更概述

本次品牌更名涉及项目从「HydraFlow」到「清悦印象」的全面升级，包括：

- 项目名称、版本号更新
- 前端 UI 显示名称调整
- 后端 API 标题和文档更新
- localStorage 存储键名迁移
- 异常类名和日志模块重命名
- 配置文件更新

---

## 二、详细变更清单

### 2.1 前端文件更新

| 文件路径 | 变更内容 | 变更类型 |
|----------|----------|----------|
| `ui/package.json` | 项目名称 `hydraflow-ui` → `qingyue-yinxiang-ui` | 修改 |
| `ui/package.json` | 描述更新为「清悦印象 - 企业级智能工作流引擎」 | 修改 |
| `ui/index.html` | 页面标题更新为「清悦印象 - 企业级智能工作流引擎」 | 修改 |
| `ui/index.html` | Meta description 更新 | 修改 |
| `ui/src/stores/theme.ts` | localStorage 键名 `hydraflow_theme` → `qingyue-yinxiang_theme` | 修改 |
| `ui/src/stores/theme.ts` | localStorage 键名 `hydraflow_language` → `qingyue-yinxiang_language` | 修改 |
| `ui/src/stores/authStore.ts` | localStorage 键名 `hydraflow_api_settings` → `qingyue-yinxiang_api_settings` | 修改 |
| `ui/src/views/ApiView.vue` | localStorage 键名 `hydraflow_api_settings` → `qingyue-yinxiang_api_settings` | 修改 |
| `ui/src/views/SystemView.vue` | 系统名称 `HydraFlow AI` → `清悦印象 AI` | 修改 |
| `ui/src/components/AppSidebar.vue` | Logo 字母 `H` → `Q` | 修改 |
| `ui/src/components/AppSidebar.vue` | 副标题「清新淡雅，悦己，给时间留下点印象」 | 新增 |
| `ui/src/stores/pluginStore.ts` | 团队名称 `HydraFlow Team` → `清悦印象团队` | 修改 |

### 2.2 后端文件更新

| 文件路径 | 变更内容 | 变更类型 |
|----------|----------|----------|
| `pyproject.toml` | 项目名称 `hydraflow-ai` → `qingyue-yinxiang-ai` | 修改 |
| `pyproject.toml` | 版本 `1.1.0` → `2.0.0` | 修改 |
| `pyproject.toml` | 描述更新为「清悦印象 - 企业级智能工作流引擎」 | 修改 |
| `pyproject.toml` | 作者更新为「清悦印象开发团队」 | 修改 |
| `pyproject.toml` | CLI 脚本 `hydraflow` → `qingyue-yinxiang` | 修改 |
| `src/api/app.py` | FastAPI title `HydraFlow AI` → `清悦印象 AI` | 修改 |
| `src/api/app.py` | FastAPI description 更新 | 修改 |
| `src/api/app.py` | 版本 `1.1.0` → `2.0.0` | 修改 |
| `src/api/app.py` | 日志模块 `hydraflow.api` → `qingyue-yinxiang.api` | 修改 |
| `src/api/app.py` | 启动日志更新 | 修改 |
| `src/api/app.py` | 异常类 `HydraFlowError` → `QingYueYinXiangError` | 修改 |
| `src/api/api_routes.py` | 系统信息 API 返回 `name: "HydraFlow AI"` → `name: "清悦印象 AI"` | 修改 |
| `src/api/api_routes.py` | 版本 `1.1.0` → `2.0.0` | 修改 |
| `src/core/config.py` | 模块文档注释更新 | 修改 |
| `src/core/exceptions.py` | 基础异常类 `HydraFlowError` → `QingYueYinXiangError` | 修改 |
| `src/core/exceptions.py` | 所有子类异常继承链更新 | 修改 |
| `src/core/exceptions.py` | 模块文档注释更新 | 修改 |

---

## 三、数据迁移说明

### 3.1 localStorage 迁移

由于 localStorage 键名变更，用户之前的主题、语言和 API 设置将被重置。需要用户重新配置。

如需手动迁移数据，可在浏览器控制台执行：

```javascript
// 主题设置迁移
const theme = localStorage.getItem('hydraflow_theme');
if (theme) localStorage.setItem('qingyue-yinxiang_theme', theme);

// 语言设置迁移
const lang = localStorage.getItem('hydraflow_language');
if (lang) localStorage.setItem('qingyue-yinxiang_language', lang);

// API 设置迁移
const apiSettings = localStorage.getItem('hydraflow_api_settings');
if (apiSettings) localStorage.setItem('qingyue-yinxiang_api_settings', apiSettings);
```

---

## 四、样式适配验证

### 4.1 侧边栏组件 (`AppSidebar.vue`)

- ✅ Logo 字母已从 `H` 更新为 `Q`
- ✅ 标题「清悦印象」正确显示
- ✅ 副标题「清新淡雅，悦己，给时间留下点印象」正确显示
- ✅ 文字溢出使用 `text-overflow: ellipsis` 处理
- ✅ 响应式布局在移动端隐藏侧边栏

### 4.2 设置页面 (`SystemView.vue`)

- ✅ 系统名称显示为「清悦印象 AI」
- ✅ 表单布局正常，宽度适配新名称长度

---

## 五、API 验证结果

| 检查项 | 状态 | 验证命令 |
|--------|------|----------|
| 健康检查版本 | ✅ 通过 | `curl http://localhost:8000/health` |
| API 文档标题 | ✅ 通过 | `curl http://localhost:8000/openapi.json` |
| 系统信息 API | ✅ 通过 | `curl http://localhost:8000/api/v1/system/info` |

---

## 六、后续建议

### 6.1 可选优化项

1. **后端日志模块重命名**：当前后端代码中仍有大量 `logging.getLogger("hydraflow.*")` 调用，可选择性地更新为 `qingyue-yinxiang.*`（非必须，属于内部实现细节）

2. **文档归档**：建议将旧版本文档移至 `docs/archive/` 目录

3. **数据库迁移脚本**：如项目使用数据库存储配置，可能需要数据库迁移脚本更新配置中的品牌名称

### 6.2 不建议修改的内容

1. **代码注释和内部变量名**：保持代码可读性和历史追溯性
2. **备份文件** (`docs/archive/` 目录)：保留历史备份
3. **第三方依赖配置**：如 gRPC 服务名称等

---

## 七、变更统计

| 分类 | 数量 |
|------|------|
| 前端文件更新 | 8 个 |
| 后端文件更新 | 8 个 |
| localStorage 键名变更 | 4 个 |
| API 响应字段更新 | 4 处 |
| 异常类重命名 | 1 个基础类 + 18 个子类 |

---

> **注意**：本次变更不包含任何功能逻辑修改，仅为品牌名称和配置的更新。
