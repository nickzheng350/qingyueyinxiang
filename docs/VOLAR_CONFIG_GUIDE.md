# Volar 插件配置指南

## 目录

1. [为什么需要切换到 Volar](#为什么需要切换到-volar)
2. [手动配置步骤](#手动配置步骤)
3. [VS Code 设置推荐](#vs-code-设置推荐)
4. [类型声明配置](#类型声明配置)
5. [验证配置是否生效](#验证配置是否生效)
6. [常见问题](#常见问题)

---

## 为什么需要切换到 Volar

### Vetur 的问题
- ✖️ 已停止维护，不再更新
- ✖️ 不支持 Vue 3 Composition API
- ✖️ 不支持 TypeScript 严格模式
- ✖️ 路径别名解析有问题
- ✖️ `.vue` 文件类型推断不准确

### Volar 的优势
- ✅ 官方推荐的 Vue 语言支持
- ✅ 完美支持 Vue 3 + TypeScript
- ✅ 支持 Composition API 和 `<script setup>`
- ✅ 准确的类型推断
- ✅ 更好的性能和稳定性

---

## 手动配置步骤

### 步骤 1：禁用 Vetur 插件

1. 打开 VS Code
2. 按下 `Ctrl+Shift+X`（或点击左侧扩展图标）
3. 在搜索框中输入 `Vetur`
4. 找到 Vetur 插件，点击「禁用」按钮

### 步骤 2：安装 Volar 插件

1. 在扩展市场搜索框中输入 `Volar`
2. 找到 `Vue Language Features (Volar)` 插件
3. 点击「安装」按钮

### 步骤 3：安装 TypeScript Vue Plugin

1. 在扩展市场搜索框中输入 `TypeScript Vue Plugin`
2. 找到 `TypeScript Vue Plugin (Volar)` 插件
3. 点击「安装」按钮

### 步骤 4：重启 VS Code

1. 关闭 VS Code 窗口
2. 重新打开项目

---

## VS Code 设置推荐

### 在 settings.json 中添加以下配置

```json
{
  // 禁用 Vetur（如果仍有残留）
  "vetur.enable": false,
  
  // 配置 Volar
  "vue.autoInsert.dotValue": true,
  "vue.codeActions.enabled": true,
  "vue.complete.completeFunctionCalls": true,
  "vue.complete.useScaffoldSnippets": true,
  
  // TypeScript 配置
  "typescript.preferences.importModuleSpecifier": "non-relative",
  "typescript.preferences.quoteStyle": "single",
  
  // 路径别名支持（已在 jsconfig.json 中配置）
  "javascript.preferences.importModuleSpecifier": "non-relative"
}
```

### 快速打开 settings.json

- Windows/Linux: `Ctrl+,` → 点击右上角「打开设置(JSON)」
- macOS: `Cmd+,` → 点击右上角「打开设置(JSON)」

---

## 类型声明配置

### 项目中已有的类型声明文件

**文件**: `src/shims-vue.d.ts`

```typescript
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '@/components/SkillCard.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{
    skill: any
    showToggle?: boolean
    showInstall?: boolean
  }, {}, {}>
  export default component
}

declare module '@/stores/skillStore' {
  import { Store } from 'pinia'
  
  interface SkillState {
    installed: any[]
    market: any[]
    loading: boolean
  }
  
  interface SkillStore extends Store<string, SkillState> {
    fetchInstalled(): Promise<void>
    fetchMarket(): Promise<void>
  }
  
  export function useSkillStore(): SkillStore
}

declare module '@/stores/theme' {
  import { Store } from 'pinia'
  import { Ref } from 'vue'
  
  interface ThemeState {
    language: Ref<string>
  }
  
  interface ThemeStore extends Store<string, ThemeState> {}
  
  export function useThemeStore(): ThemeStore
}

declare module '@/api/client' {
  export const client: {
    get(url: string): Promise<any>
    post(url: string, data?: any): Promise<any>
  }
}

declare module '@/stores/modelStore' {
  import { Store } from 'pinia'
  import { Ref } from 'vue'
  
  interface ModelState {
    models: any[]
    loading: boolean
  }
  
  interface ModelStore extends Store<string, ModelState> {
    fetchModels(): Promise<void>
    addModel(model: any): Promise<void>
    deleteModel(id: string): Promise<void>
    toggleModel(id: string): Promise<void>
  }
  
  export function useModelStore(): ModelStore
}
```

### 路径别名配置

**文件**: `jsconfig.json`

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    },
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler"
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.vue"],
  "exclude": ["node_modules", "dist"]
}
```

---

## 验证配置是否生效

### 验证步骤

1. **打开 ModelView.vue**
   - 路径：`src/views/ModelView.vue`
   - 检查第 213-214 行的导入语句
   - 应该不再显示 "Cannot find module" 错误

2. **打开 SkillsView.vue**
   - 路径：`src/views/SkillsView.vue`
   - 检查第 74-78 行的导入语句
   - 应该不再显示 "Cannot find module" 错误

3. **运行构建命令**
   ```bash
   cd ui
   npm run build
   ```
   - 构建应该成功完成

4. **运行测试**
   ```bash
   cd ui
   npm run test
   ```
   - 所有测试应该通过

### 验证标准

| 验证项 | 成功标志 |
|--------|----------|
| 导入报错 | 不再显示 `Cannot find module '@/...'` |
| 类型提示 | 参数不再显示 `implicitly has an 'any' type` |
| 构建 | `npm run build` 成功 |
| 测试 | `npm run test` 全部通过 |

---

## 常见问题

### Q1: Volar 安装后仍然报错？

**解决方案：**
1. 确保已禁用 Vetur
2. 重启 VS Code
3. 删除 `.vscode/.volar` 目录（如果存在）
4. 执行 `Ctrl+Shift+P` → `Vue: Restart Vue Language Server`

### Q2: 路径别名 `@/*` 仍然无法识别？

**解决方案：**
1. 确保 `jsconfig.json` 或 `tsconfig.json` 中配置了路径别名
2. 检查配置文件是否在项目根目录
3. 重启 Vue Language Server

### Q3: 类型推断仍然不准确？

**解决方案：**
1. 确保类型声明文件 (`shims-vue.d.ts`) 完整
2. 检查 `tsconfig.json` 中是否包含了所有需要的文件
3. 尝试删除 `node_modules/.cache` 目录

### Q4: 构建成功但编辑器仍报错？

**解决方案：**
1. 这可能是缓存问题
2. 执行 `Ctrl+Shift+P` → `Developer: Reload Window`
3. 或重启 VS Code

---

## 配置检查清单

✅ Vetur 已禁用
✅ Volar 已安装
✅ TypeScript Vue Plugin 已安装
✅ jsconfig.json 已配置路径别名
✅ shims-vue.d.ts 包含所有模块声明
✅ 项目构建成功
✅ 项目测试通过

---

**文档版本**: v1.0.0  
**适用项目**: HydraFlow AI  
**更新日期**: 2026年5月