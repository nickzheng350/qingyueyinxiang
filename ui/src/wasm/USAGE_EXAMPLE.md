# WASM 技能引擎使用示例

## 在 Vue 组件中使用

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { initWasm, install_skill } from '@/wasm'

const loading = ref(false)
const installResult = ref<any>(null)

onMounted(async () => {
  try {
    await initWasm()
    console.log('WASM 初始化完成')
  } catch (error) {
    console.error('WASM 初始化失败:', error)
  }
})

async function handleInstall() {
  loading.value = true
  try {
    installResult.value = await install_skill(
      'my_skill',
      '/path/to/skill.tar.gz'
    )
    console.log('安装结果:', installResult.value)
  } catch (error) {
    console.error('安装失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <button @click="handleInstall" :disabled="loading">
      {{ loading ? '安装中...' : '安装技能' }}
    </button>
    
    <div v-if="installResult">
      <p>状态: {{ installResult.success ? '成功' : '失败' }}</p>
      <p>消息: {{ installResult.message }}</p>
    </div>
  </div>
</template>
```

## API 参考

### initWasm()

初始化 WASM 模块。必须在调用其他函数前执行。

```typescript
await initWasm()
```

### install_skill(skillId: string, tarPath: string)

安装技能。

```typescript
const result = await install_skill('skill_id', '/path/to/file.tar.gz')
// 返回: { success: boolean, skill_id: string, message: string }
```

### uninstall_skill(skillId: string)

卸载技能。

```typescript
await uninstall_skill('skill_id')
```

### list_skills()

列出所有技能。

```typescript
const skills = await list_skills()
// 返回: Skill[]
```

## 性能监控

```typescript
console.time('install')
await install_skill('skill_id', '/path/to/file.tar.gz')
console.timeEnd('install')
// 输出: install: 15.2ms
```

## 错误处理

```typescript
try {
  const result = await install_skill('skill_id', '/path/to/file.tar.gz')
  if (result.success) {
    console.log('安装成功')
  } else {
    console.error('安装失败:', result.message)
  }
} catch (error) {
  console.error('异常:', error)
}
```
