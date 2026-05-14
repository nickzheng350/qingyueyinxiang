<template>
  <div class="card">
    <div class="card-header">
      <div><div class="card-title">📁 文件管理</div><div class="card-subtitle">管理存储中的文件，支持上传、下载和删除</div></div>
      <div style="display: flex; gap: 0.5rem;">
        <button class="btn btn-primary" @click="uploadVisible = true">📤 上传文件</button>
        <button class="btn btn-secondary" @click="fetchFiles">🔄 刷新</button>
      </div>
    </div>
    <div class="file-stats">
      <div><div class="stat-num">{{ files.length }}</div><div class="stat-label">文件数</div></div>
      <div><div class="stat-num">0 GB</div><div class="stat-label">已使用</div></div>
      <div><div class="stat-num">基础</div><div class="stat-label">存储级别</div></div>
      <div><div class="stat-num">✅</div><div class="stat-label">本地存储</div></div>
    </div>
    <div v-if="!files.length" class="empty-state">
      <div style="font-size: 3rem;">📂</div>
      <p>暂无文件</p>
      <button class="btn btn-primary" style="margin-top:1rem;" @click="uploadVisible = true">上传文件</button>
    </div>
    <el-table v-else :data="files" size="small">
      <el-table-column prop="name" label="文件名" />
      <el-table-column prop="size" label="大小" width="100" />
      <el-table-column prop="time" label="修改时间" width="160" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <button class="btn btn-text btn-sm">下载</button>
          <button class="btn btn-danger btn-sm">删除</button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="uploadVisible" title="📤 上传文件" width="500px">
      <el-form>
        <el-form-item label="选择文件"><el-upload :auto-upload="false" multiple><button class="btn btn-secondary">选择文件</button></el-upload></el-form-item>
        <el-form-item label="目标目录"><el-input placeholder="留空则上传到根目录" /></el-form-item>
      </el-form>
      <template #footer><button class="btn btn-secondary" @click="uploadVisible = false">取消</button><button class="btn btn-primary">开始上传</button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const files = ref<any[]>([])
const uploadVisible = ref(false)
function fetchFiles() { files.value = [] }
</script>

<style scoped>
.card { background: linear-gradient(145deg, var(--bg-card), var(--bg-dark)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }
.file-stats { display: flex; gap: 2rem; margin-bottom: 1.5rem; padding: 1rem; background: var(--bg-dark); border-radius: 8px; }
.stat-num { font-size: 1.5rem; font-weight: bold; }
.stat-label { font-size: 0.85rem; color: var(--text-secondary); }
.empty-state { text-align: center; color: var(--text-secondary); padding: 3rem; }
:deep(.el-table) { background: transparent !important; --el-table-bg-color: transparent; color: var(--text-primary); }
:deep(.el-table th.el-table__cell) { background: var(--bg-hover) !important; color: var(--text-secondary); }
</style>