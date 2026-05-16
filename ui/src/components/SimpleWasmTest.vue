<template>
  <div class="simple-wasm-test">
    <h3>🔧 WASM 技能引擎测试</h3>
    
    <!-- 初始化状态 -->
    <div class="status-box" :class="statusClass">
      <div class="status-icon">{{ statusIcon }}</div>
      <div class="status-text">{{ statusText }}</div>
    </div>

    <!-- 初始化按钮 -->
    <button 
      @click="initializeWasm" 
      :disabled="isInitializing"
      class="btn btn-primary mt-4"
    >
      {{ isInitializing ? '初始化中...' : '初始化 WASM' }}
    </button>

    <!-- 测试操作 -->
    <div v-if="wasmReady" class="test-section">
      <h4>测试操作</h4>
      
      <div class="test-grid">
        <div class="test-item">
          <button @click="testListSkills" class="btn btn-secondary">列出技能</button>
          <div v-if="listResult" class="result-box">
            <pre>{{ JSON.stringify(listResult, null, 2) }}</pre>
          </div>
        </div>
        
        <div class="test-item">
          <button @click="testInstallSkill" class="btn btn-secondary">安装测试技能</button>
          <div v-if="installResult" class="result-box">
            <pre>{{ JSON.stringify(installResult, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- 错误信息 -->
    <div v-if="errorMessage" class="error-box">
      <span class="error-icon">❌</span>
      <span class="error-text">{{ errorMessage }}</span>
    </div>

    <!-- 日志 -->
    <div class="log-box">
      <h4>📜 日志</h4>
      <div class="log-content">
        <div v-for="(log, index) in logs" :key="index" class="log-item">
          <span class="log-time">{{ log.time }}</span>
          <span :class="['log-level', log.level]">{{ log.level }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

// WASM 状态
const wasmReady = ref(false)
const isInitializing = ref(false)
const errorMessage = ref('')

// 测试结果
const listResult = ref<any>(null)
const installResult = ref<any>(null)

// 日志
const logs = ref<Array<{ time: string; level: string; message: string }>>([])

function addLog(message: string, level: string = 'INFO') {
  const now = new Date()
  const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  logs.value.push({ time: timeStr, level, message })
}

// 状态计算
const statusClass = computed(() => {
  if (errorMessage.value) return 'status-error'
  if (wasmReady.value) return 'status-success'
  if (isInitializing.value) return 'status-loading'
  return 'status-default'
})

const statusIcon = computed(() => {
  if (errorMessage.value) return '❌'
  if (wasmReady.value) return '✅'
  if (isInitializing.value) return '⏳'
  return '❓'
})

const statusText = computed(() => {
  if (errorMessage.value) return 'WASM 初始化失败'
  if (wasmReady.value) return 'WASM 已就绪'
  if (isInitializing.value) return '正在初始化...'
  return 'WASM 未初始化'
})

// 初始化 WASM
async function initializeWasm() {
  if (wasmReady.value || isInitializing.value) return
  
  isInitializing.value = true
  errorMessage.value = ''
  
  try {
    addLog('开始初始化 WASM 技能引擎...', 'INFO')
    
    // 动态导入 WASM 模块
    const { init_wasm } = await import('@/wasm/skill_engine.js')
    
    addLog('加载 WASM 模块...', 'INFO')
    await init_wasm()
    
    wasmReady.value = true
    addLog('WASM 初始化成功！', 'SUCCESS')
    
  } catch (error: any) {
    errorMessage.value = error.message || 'WASM 初始化失败'
    addLog(`WASM 初始化失败: ${error.message}`, 'ERROR')
  } finally {
    isInitializing.value = false
  }
}

// 测试列出技能
async function testListSkills() {
  if (!wasmReady.value) return
  
  try {
    addLog('测试列出技能...', 'INFO')
    
    const { list_skills } = await import('@/wasm/skill_engine.js')
    const result = await list_skills()
    
    listResult.value = result
    addLog(`成功获取 ${result.length} 个技能`, 'SUCCESS')
    
  } catch (error: any) {
    addLog(`列出技能失败: ${error.message}`, 'ERROR')
  }
}

// 测试安装技能
async function testInstallSkill() {
  if (!wasmReady.value) return
  
  try {
    addLog('测试安装技能...', 'INFO')
    
    const { install_skill } = await import('@/wasm/skill_engine.js')
    
    // 创建测试数据（模拟 tar.gz 文件内容）
    const testData = new Uint8Array([1, 2, 3, 4, 5])
    const skillId = `test_skill_${Date.now()}`
    
    const result = await install_skill(skillId, testData)
    
    installResult.value = result
    addLog(`技能安装结果: ${result?.success ? '成功' : '失败'}`, result?.success ? 'SUCCESS' : 'ERROR')
    
  } catch (error: any) {
    addLog(`安装技能失败: ${error.message}`, 'ERROR')
  }
}

onMounted(() => {
  addLog('组件已挂载', 'INFO')
})
</script>

<style scoped>
.simple-wasm-test {
  padding: 1.5rem;
  background: var(--bg-dark);
  border-radius: 12px;
}

.status-box {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  transition: all 0.3s;
}

.status-default {
  background: rgba(156, 163, 175, 0.1);
  border: 1px solid rgba(156, 163, 175, 0.3);
}

.status-loading {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.status-success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.status-error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.status-icon {
  font-size: 1.5rem;
}

.status-text {
  font-weight: 500;
}

.test-section {
  margin-top: 1.5rem;
}

.test-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 1rem;
}

.test-item {
  background: rgba(255, 255, 255, 0.05);
  padding: 1rem;
  border-radius: 8px;
}

.result-box {
  margin-top: 1rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  max-height: 150px;
  overflow-y: auto;
}

.result-box pre {
  font-size: 0.75rem;
  color: #9ca3af;
}

.error-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
}

.error-icon {
  color: #ef4444;
}

.error-text {
  color: #fca5a5;
}

.log-box {
  margin-top: 1.5rem;
}

.log-content {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 0.75rem;
}

.log-item {
  display: flex;
  gap: 0.5rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.log-time {
  color: #6b7280;
}

.log-level {
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.65rem;
}

.log-level.INFO {
  color: #6b7280;
}

.log-level.SUCCESS {
  color: #22c55e;
}

.log-level.ERROR {
  color: #ef4444;
}

.log-message {
  color: #e5e7eb;
}
</style>
