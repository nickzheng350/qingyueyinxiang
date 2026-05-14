import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'

export interface Task {
  id: string
  name: string
  status: 'running' | 'success' | 'pending' | 'error'
  progress: number
  time: string
}

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const loading = ref(false)

  async function fetchTasks() {
    loading.value = true
    try {
      const data = await client.get('/tasks')
      tasks.value = data.tasks || []
    } catch {
      // fallback mock data
      tasks.value = [
        { id: 'T001', name: '模型训练任务', status: 'running', progress: 67, time: '5分钟前' },
        { id: 'T002', name: '数据处理', status: 'success', progress: 100, time: '15分钟前' },
        { id: 'T003', name: '图片生成批量任务', status: 'pending', progress: 0, time: '30分钟前' },
        { id: 'T004', name: '音频合成', status: 'error', progress: 34, time: '1小时前' },
      ]
    } finally {
      loading.value = false
    }
  }

  return { tasks, loading, fetchTasks }
})