<template>
  <div>
    <!-- 统计卡片 -->
    <div class="grid-4">
      <StatCard icon="💻" label="CPU 使用率" :value="stats.cpu + '%'" :progress="stats.cpu" color="cpu" />
      <StatCard icon="🧠" label="内存使用" :value="stats.memory + ' GB'" :progress="stats.memory * 2" color="memory" />
      <StatCard icon="🎮" label="GPU 使用率" :value="stats.gpu + '%'" :progress="stats.gpu" color="gpu" />
      <StatCard icon="📦" label="存储使用" :value="stats.storage + ' GB'" :progress="stats.storage / 2" color="cpu" />
    </div>

    <div class="grid-2">
      <!-- 系统健康状态 -->
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">系统健康状态</div>
            <div class="card-subtitle">实时监控系统运行状态</div>
          </div>
          <span class="status-badge status-success">✓ 健康</span>
        </div>
        <div style="display: flex; gap: 1rem; align-items: center;">
          <div style="flex: 1;">
            <div v-for="item in healthItems" :key="item.label" class="health-row">
              <span class="health-label">{{ item.label }}</span>
              <span>{{ item.value }}</span>
            </div>
          </div>
          <div class="health-circle">100%</div>
        </div>
      </div>

      <!-- 最近任务 -->
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">最近任务</div>
            <div class="card-subtitle">最近执行的任务列表</div>
          </div>
          <button class="btn-config" @click="$router.push('/tasks')">{{ lang === 'zh' ? '查看全部' : 'View All' }}</button>
        </div>
        <el-table :data="recentTasks" size="small" style="background: transparent;">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <span :class="`status-badge status-${row.status}`">{{ statusText[row.status] }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="time" label="时间" width="80" />
        </el-table>
      </div>
    </div>

    <!-- 快速操作 -->
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">快速操作</div>
          <div class="card-subtitle">一键执行常用操作</div>
        </div>
      </div>
      <div class="grid-auto">
        <button 
          v-for="op in quickActions" 
          :key="op.label" 
          :class="['quick-btn', op.primary ? 'btn-primary' : 'btn-secondary']"
          @click="op.path && $router.push(op.path)"
        >
          <span class="quick-icon">{{ op.icon }}</span>
          <span>{{ op.label }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import StatCard from '@/components/StatCard.vue'
import { useThemeStore } from '@/stores/theme'
import { storeToRefs } from 'pinia'

const themeStore = useThemeStore()
const { language: lang } = storeToRefs(themeStore)

const stats = ref({ cpu: 24, memory: 4.2, gpu: 0, storage: 128 })
const recentTasks = ref([
  { id: 'T001', name: '模型训练任务', status: 'running', time: '5分钟前' },
  { id: 'T002', name: '数据处理', status: 'success', time: '15分钟前' },
  { id: 'T003', name: '图片生成批量任务', status: 'pending', time: '30分钟前' },
])
const statusText: Record<string, string> = { running: '运行中', success: '已完成', pending: '等待中', error: '失败' }

const healthItems = [
  { label: 'API 响应', value: '12ms' },
  { label: '数据库连接', value: '✓ 正常' },
  { label: '缓存状态', value: '✓ 正常' },
  { label: '任务队列', value: '0 等待' },
]

const quickActions = [
  { icon: '✨', label: '生成内容', path: '/generative', primary: true },
  { icon: '🔄', label: '创建流水线', path: '/workflow' },
  { icon: '🏪', label: '浏览技能市场', path: '/market' },
  { icon: '🔄', label: '刷新状态', path: '' },
]

function updateStats() {
  stats.value = {
    cpu: Math.floor(Math.random() * 60 + 20),
    memory: parseFloat((Math.random() * 8 + 2).toFixed(1)),
    gpu: Math.floor(Math.random() * 30),
    storage: Math.floor(Math.random() * 40 + 100),
  }
}

onMounted(() => {
  updateStats()
})
</script>

<style scoped>
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; margin-bottom: 1.5rem; }
.grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; margin-bottom: 1.5rem; }
.grid-auto { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 1rem; }

.card {
  background: linear-gradient(145deg, var(--bg-card), var(--bg-dark));
  border-radius: 16px;
  border: 1px solid var(--border);
  padding: 1.75rem;
  color: var(--text-primary);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}

.card-title { font-size: 1.1rem; font-weight: 600; color: var(--text-primary); }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }

.btn-primary {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--primary) 30%, transparent);
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  color: var(--text-primary);
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s;
}

.btn-secondary:hover {
  border-color: var(--primary);
}

.btn-config {
  padding: 0.35rem 0.75rem;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.3s;
}

.btn-config:hover {
  border-color: var(--primary);
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
}
.status-success { background: color-mix(in srgb, var(--success) 20%, transparent); color: var(--success); }
.status-running { background: color-mix(in srgb, var(--primary) 20%, transparent); color: white; }
.status-pending { background: color-mix(in srgb, var(--warning) 20%, transparent); color: var(--warning); }
.status-error { background: color-mix(in srgb, var(--danger) 20%, transparent); color: var(--danger); }

.health-row { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
.health-label { color: var(--text-secondary); }
.health-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--success) 10%, transparent);
  border: 3px solid var(--success);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
}

.quick-btn {
  display: flex;
  flex-direction: column;
  padding: 1.5rem !important;
  height: auto;
  border-radius: 12px;
}
.quick-icon { font-size: 2rem; margin-bottom: 0.5rem; }

:deep(.el-table) {
  background: transparent !important;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: var(--bg-hover);
  color: var(--text-primary);
}
:deep(.el-table th.el-table__cell) {
  background: var(--bg-hover) !important;
  color: var(--text-secondary);
}
</style>