# WASM 技能引擎使用指南

## 快速开始

### 1. 初始化 WASM

在 Vue 组件中初始化 WASM 模块：

```typescript
import { initWasm, install_skill } from '@/wasm'

// 在应用启动时初始化
await initWasm()
```

### 2. 使用技能安装功能

```typescript
import { install_skill } from '@/wasm'

async function handleInstall(skillId: string, tarPath: string) {
  try {
    const result = await install_skill(skillId, tarPath)
    console.log('安装成功:', result)
  } catch (error) {
    console.error('安装失败:', error)
  }
}
```

### 3. 在 Vue 组件中使用

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { initWasm, install_skill } from '@/wasm'

const loading = ref(false)
const progress = ref(0)

onMounted(async () => {
  await initWasm()
  console.log('WASM 初始化完成')
})

async function handleInstall() {
  loading.value = true
  try {
    const result = await install_skill('test_skill', '/path/to/file.tar.gz')
    console.log('安装完成:', result)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <button @click="handleInstall" :disabled="loading">
    {{ loading ? '安装中...' : '安装技能' }}
  </button>
</template>
```

## API 参考

### initWasm()

初始化 WASM 模块，必须在调用其他函数前执行。

```typescript
await initWasm()
```

### install_skill(skillId: string, tarPath: string): Promise<Skill>

安装技能。

**参数:**
- `skillId`: 技能 ID
- `tarPath`: tar.gz 文件路径

**返回:**
- `Promise<Skill>`: 安装后的技能对象

### uninstall_skill(skillId: string): Promise<void>

卸载技能。

**参数:**
- `skillId`: 技能 ID

### list_skills(): Promise<Skill[]>

列出所有已安装的技能。

**返回:**
- `Promise<Skill[]>`: 技能列表

## 性能优化

### 1. 预加载 WASM

在应用启动时预加载：

```typescript
// main.ts
import { initWasm } from '@/wasm'

async function bootstrap() {
  await initWasm()
  createApp(App).mount('#app')
}

bootstrap()
```

### 2. 懒加载

按需加载 WASM 模块：

```typescript
const loadWasm = async () => {
  const wasm = await import('@/wasm')
  await wasm.initWasm()
  return wasm
}
```

## 故障排查

### WASM 加载失败

检查浏览器控制台是否有 CORS 错误，确保服务器正确配置 MIME 类型：

```
application/wasm
```

### 性能问题

使用 Chrome DevTools 的 Performance 面板分析 WASM 执行性能。

## 构建

重新构建 WASM:

```bash
./scripts/build_wasm.sh
```
