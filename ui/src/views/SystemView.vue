<template>
  <div class="card">
    <div class="card-header">
      <div><div class="card-title">🔧 系统设置</div><div class="card-subtitle">配置系统参数</div></div>
    </div>
    <div class="grid-2">
      <div>
        <el-form label-position="top">
          <el-form-item label="系统名称"><el-input v-model="form.name" disabled /></el-form-item>
          <el-form-item label="运行环境"><el-select v-model="form.env" style="width:100%"><el-option value="development" label="development" /><el-option value="staging" label="staging" /><el-option value="production" label="production" /></el-select></el-form-item>
          <el-form-item label="调试模式"><el-switch v-model="form.debug" active-text="开启" inactive-text="关闭" /></el-form-item>
        </el-form>
      </div>
      <div>
        <el-form label-position="top">
          <el-form-item label="API 端口"><el-input-number v-model="form.port" :min="1" :max="65535" style="width:100%" /></el-form-item>
          <el-form-item label="工作进程数"><el-input-number v-model="form.workers" :min="1" :max="32" style="width:100%" /></el-form-item>
          <el-form-item label="日志级别"><el-select v-model="form.logLevel" style="width:100%"><el-option value="DEBUG" label="DEBUG" /><el-option value="INFO" label="INFO" /><el-option value="WARNING" label="WARNING" /><el-option value="ERROR" label="ERROR" /></el-select></el-form-item>
        </el-form>
      </div>
    </div>
    <el-button type="primary" style="margin-top: 1rem;" @click="saveSystemSettings">保存设置</el-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const form = ref({ name: 'HydraFlow AI', env: 'development', debug: true, port: 8080, workers: 4, logLevel: 'INFO' })
function saveSystemSettings() { console.log('save', form.value) }
</script>

<style scoped>
.card { background: linear-gradient(145deg, var(--bg-card), rgba(15, 23, 42, 0.8)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
</style>