<template>
  <div class="card">
    <div class="card-header">
      <div><div class="card-title">✏️ 提示词管理</div><div class="card-subtitle">创建和管理AI提示词</div></div>
      <button class="btn btn-primary" @click="promptVisible = true">➕ 新建提示词</button>
    </div>
    <div class="grid-2">
      <div>
        <el-form label-position="top">
          <el-form-item label="提示词名称"><el-input v-model="form.name" placeholder="输入提示词名称" /></el-form-item>
          <el-form-item label="提示词类型"><el-select v-model="form.type" style="width:100%">
            <el-option value="system" label="系统提示词" /><el-option value="user" label="用户提示词" /><el-option value="assistant" label="助手提示词" />
          </el-select></el-form-item>
          <el-form-item label="提示词内容"><el-input v-model="form.content" type="textarea" :rows="10" placeholder="输入提示词内容..." @input="updatePreview" /></el-form-item>
          <button class="btn btn-primary" @click="savePrompt">保存提示词</button>
        </el-form>
      </div>
      <div>
        <div style="margin-bottom: 0.5rem; color: var(--text-secondary); font-size: 0.85rem;">预览效果</div>
        <div class="preview-box">{{ preview || '预览将在这里显示...' }}</div>
      </div>
    </div>
    <el-dialog v-model="promptVisible" title="➕ 新建提示词" width="500px">
      <el-form label-position="top">
        <el-form-item label="提示词名称"><el-input v-model="newPrompt.name" /></el-form-item>
        <el-form-item label="类型"><el-select v-model="newPrompt.type" style="width:100%">
          <el-option value="system" label="系统提示词" /><el-option value="user" label="用户提示词" /><el-option value="assistant" label="助手提示词" />
        </el-select></el-form-item>
        <el-form-item label="内容"><el-input v-model="newPrompt.content" type="textarea" :rows="6" /></el-form-item>
      </el-form>
      <template #footer><button class="btn btn-secondary" @click="promptVisible = false">取消</button><button class="btn btn-primary" @click="createPrompt">创建</button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const form = ref({ name: '', type: 'system', content: '' })
const preview = ref('')
const promptVisible = ref(false)
const newPrompt = ref({ name: '', type: 'system', content: '' })
function updatePreview() { preview.value = form.value.content }
function savePrompt() { console.log('save', form.value) }
function createPrompt() { promptVisible.value = false; newPrompt.value = { name: '', type: 'system', content: '' } }
</script>

<style scoped>
.card { background: linear-gradient(145deg, var(--bg-card), var(--bg-dark)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.preview-box { background: var(--bg-dark); border-radius: 8px; padding: 1rem; min-height: 350px; white-space: pre-wrap; color: var(--text-secondary); }
</style>