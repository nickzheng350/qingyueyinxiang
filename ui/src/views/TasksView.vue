<template>
  <div class="card">
    <div class="card-header">
      <div><div class="card-title">📋 任务管理</div><div class="card-subtitle">管理和监控系统任务</div></div>
      <el-button type="primary" @click="taskVisible = true">➕ 提交任务</el-button>
    </div>
    <el-table :data="tasks" size="small" v-loading="loading">
      <el-table-column prop="id" label="任务ID" width="80" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }"><span :class="`status-badge status-${row.status}`">{{ statusText[row.status] }}</span></template>
      </el-table-column>
      <el-table-column prop="progress" label="进度" width="140">
        <template #default="{ row }">
          <el-progress :percentage="row.progress" :status="row.status === 'success' ? 'success' : row.status === 'error' ? 'exception' : undefined" />
        </template>
      </el-table-column>
      <el-table-column prop="time" label="创建时间" width="100" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" link type="primary" v-if="row.status === 'running'">停止</el-button>
          <el-button size="small" link type="danger">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="taskVisible" title="➕ 提交任务" width="500px">
      <el-form label-position="top">
        <el-form-item label="任务名称"><el-input v-model="newTask.name" placeholder="输入任务名称" /></el-form-item>
        <el-form-item label="任务描述"><el-input v-model="newTask.desc" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="taskVisible = false">取消</el-button><el-button type="primary" @click="submitTask">提交</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTaskStore } from '@/stores/taskStore'
import { storeToRefs } from 'pinia'
const store = useTaskStore()
const { tasks, loading } = storeToRefs(store)
const taskVisible = ref(false)
const newTask = ref({ name: '', desc: '' })
const statusText: Record<string, string> = { running: '运行中', success: '已完成', pending: '等待中', error: '失败' }
function submitTask() { tasks.value.unshift({ id: `T${Date.now()}`, name: newTask.value.name, status: 'pending', progress: 0, time: '刚刚' }); taskVisible.value = false; newTask.value = { name: '', desc: '' } }
onMounted(() => store.fetchTasks())
</script>

<style scoped>
.card { background: linear-gradient(145deg, var(--bg-card), rgba(15, 23, 42, 0.8)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }
.status-badge { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 500; }
.status-success { background: rgba(16, 185, 129, 0.2); color: var(--success); }
.status-running { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.status-pending { background: rgba(245, 158, 11, 0.2); color: var(--warning); }
.status-error { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
:deep(.el-table) { background: transparent !important; --el-table-bg-color: transparent; color: var(--text-primary); }
:deep(.el-table th.el-table__cell) { background: var(--bg-hover) !important; color: var(--text-secondary); }
:deep(.el-progress-bar__outer) { background: var(--bg-hover) !important; }
</style>