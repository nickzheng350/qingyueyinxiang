<template>
  <div class="card">
    <div class="card-header">
      <div><div class="card-title">🔌 API设置</div><div class="card-subtitle">输入API密钥和端点，系统将智能识别并建立连接</div></div>
    </div>
    <div style="max-width: 600px;">
      <el-form label-position="top">
        <el-form-item label="API Key">
          <el-input v-model="apiKey" type="password" placeholder="输入您的API密钥 (sk-xxx, r8-xxx, hf-xxx 等)" show-password />
          <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">支持：OpenAI(sk-), Replicate(r8-), HuggingFace(hf-), Anthropic(sk-ant-)</div>
        </el-form-item>
        <el-form-item label="API Base URL">
          <el-input v-model="apiUrl" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <div v-if="analysisResult" class="analysis-result">
          <div class="analysis-header">
            <span style="font-size: 2rem;">{{ analysisResult.icon }}</span>
            <div><div style="font-weight: 500;">已识别: {{ analysisResult.name }}</div><div style="font-size: 0.85rem; color: var(--text-secondary);">类型: {{ analysisResult.type }} · 模型: {{ analysisResult.model }}</div></div>
          </div>
        </div>
        <div style="display: flex; gap: 1rem; margin-top: 1.5rem; flex-wrap: wrap;">
          <button class="btn btn-primary" @click="analyzeAndConnect">🔍 智能分析并连接</button>
          <button class="btn btn-secondary" @click="saveSettings">💾 保存设置</button>
          <button class="btn btn-secondary" @click="loadSettings">📂 加载设置</button>
          <button class="btn btn-danger" @click="clearSettings">🗑️ 清除设置</button>
        </div>
        <div v-if="statusMessage" class="status-msg" :class="statusType">{{ statusMessage }}</div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const apiKey = ref('')
const apiUrl = ref('https://api.openai.com/v1')
const analysisResult = ref<any>(null)
const statusMessage = ref('')
const statusType = ref('success')

function detectApiType(key: string) {
  if (key.startsWith('sk-ant-')) return { type: 'anthropic', name: 'Anthropic Claude', icon: '🤖', model: 'claude-3-haiku-20240307' }
  if (key.startsWith('sk-')) return { type: 'openai', name: 'OpenAI', icon: '🔵', model: 'gpt-4' }
  if (key.startsWith('r8_')) return { type: 'replicate', name: 'Replicate', icon: '🔄', model: 'default' }
  if (key.startsWith('hf_')) return { type: 'huggingface', name: 'HuggingFace', icon: '🤗', model: 'default' }
  return { type: 'unknown', name: '未知', icon: '❓', model: 'unknown' }
}

async function analyzeAndConnect() {
  if (!apiKey.value) return
  const result = detectApiType(apiKey.value)
  analysisResult.value = result
  statusMessage.value = `✅ 已识别API类型 · ${result.name}`
  statusType.value = 'success'
}

function saveSettings() {
  localStorage.setItem('qingyue-yinxiang_api_settings', JSON.stringify({ apiKey: apiKey.value, apiUrl: apiUrl.value }))
  statusMessage.value = '✅ 设置已保存'
  statusType.value = 'success'
}

function loadSettings() {
  const raw = localStorage.getItem('qingyue-yinxiang_api_settings')
  if (raw) { const s = JSON.parse(raw); apiKey.value = s.apiKey || ''; apiUrl.value = s.apiUrl || 'https://api.openai.com/v1'; statusMessage.value = '✅ 已加载设置' }
  else statusMessage.value = '无可用设置'
  statusType.value = 'success'
}

function clearSettings() { localStorage.removeItem('qingyue-yinxiang_api_settings'); apiKey.value = ''; apiUrl.value = 'https://api.openai.com/v1'; analysisResult.value = null; statusMessage.value = '✅ 已清除' }
</script>

<style scoped>
.card { background: linear-gradient(145deg, var(--bg-card), var(--bg-dark)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }
.analysis-result { margin-top: 1rem; padding: 1rem; border-radius: 8px; background: var(--bg-dark); border: 1px solid var(--border); }
.analysis-header { display: flex; align-items: center; gap: 1rem; }
.status-msg { margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 8px; }
.status-msg.success { background: color-mix(in srgb, var(--success) 10%, transparent); border: 1px solid color-mix(in srgb, var(--success) 30%, transparent); color: var(--success); }
.status-msg.error { background: color-mix(in srgb, var(--danger) 10%, transparent); border: 1px solid color-mix(in srgb, var(--danger) 30%, transparent); color: var(--danger); }
</style>