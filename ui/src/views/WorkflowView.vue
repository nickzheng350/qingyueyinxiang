<template>
  <div>
    <!-- 流水线列表 -->
    <div class="card">
      <div class="card-header">
        <div><div class="card-title">🔄 {{ lang === 'zh' ? '工作流水线' : 'Workflow Pipelines' }}</div><div class="card-subtitle">{{ lang === 'zh' ? '创建和管理自动化工作流程' : 'Create and manage automated workflows' }}</div></div>
        <div style="display: flex; gap: 0.5rem; align-items: center;">
          <!-- 模式切换 -->
          <div class="mode-toggle">
            <button :class="{ active: workflowMode === 'smart' }" @click="workflowMode = 'smart'">
              🧠 {{ lang === 'zh' ? '智能模式' : 'Smart' }}
            </button>
            <button :class="{ active: workflowMode === 'manual' }" @click="workflowMode = 'manual'">
              🎛️ {{ lang === 'zh' ? '调整模式' : 'Manual' }}
            </button>
          </div>
          <el-button type="primary" @click="createWorkflow">➕ {{ lang === 'zh' ? '新建流水线' : 'New Pipeline' }}</el-button>
        </div>
      </div>

      <!-- 专业方向筛选 -->
      <div class="direction-filter">
        <button
          v-for="dir in professionalDirections"
          :key="dir.id"
          class="dir-btn"
          :class="{ active: activeDirection === dir.id }"
          @click="activeDirection = dir.id"
        >
          {{ dir.icon }} {{ lang === 'zh' ? dir.name : dir.nameEn }}
        </button>
      </div>

      <!-- 流水线卡片 -->
      <div class="grid-3">
        <div v-for="w in filteredWorkflows" :key="w.id" class="workflow-card" @click="loadWorkflow(w.id)">
          <div style="font-size: 2rem; margin-bottom: 1rem;">{{ w.icon }}</div>
          <div class="workflow-name">{{ w.name }}</div>
          <div class="workflow-desc">{{ w.description }}</div>
          <div style="margin-top: 1rem; display: flex; justify-content: space-between; align-items: center;">
            <span :class="`status-badge status-${w.status}`">{{ w.statusText }}</span>
            <el-button size="small" :type="w.status === 'pending' ? 'primary' : ''">
              {{ w.status === 'pending' ? (lang === 'zh' ? '⚙️ 配置' : '⚙️ Config') : (lang === 'zh' ? '▶️ 运行' : '▶️ Run') }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 流水线设计器 -->
    <div class="card" style="margin-top: 1.5rem;">
      <div class="card-header">
        <div><div class="card-title">🎨 {{ lang === 'zh' ? '流水线设计器' : 'Pipeline Designer' }}</div><div class="card-subtitle">{{ lang === 'zh' ? '可视化构建工作流程' : 'Visually build workflows' }}</div></div>
        <div style="display: flex; gap: 0.5rem;">
          <el-button size="small" @click="clearWorkflow">🗑️ {{ lang === 'zh' ? '清空' : 'Clear' }}</el-button>
          <el-button size="small" type="primary" @click="saveWorkflow">💾 {{ lang === 'zh' ? '保存' : 'Save' }}</el-button>
          <el-button size="small" type="success" @click="runWorkflow">▶️ {{ lang === 'zh' ? '运行' : 'Run' }}</el-button>
        </div>
      </div>
      <div style="display: flex; gap: 2rem;">
        <div class="node-panel">
          <div v-for="group in nodeGroups" :key="group.label">
            <div class="node-group-label">{{ group.label }}</div>
            <div v-for="node in group.nodes" :key="node.id" class="flow-node" draggable="true"
              @dragstart="dragNode($event, node.id)">
              <div class="flow-node-icon">{{ node.icon }}</div>
              <div class="flow-node-title">{{ node.title }}</div>
            </div>
          </div>
        </div>
        <div style="flex: 1;">
          <div class="canvas-area" @drop="dropNode" @dragover.prevent>
            <div v-if="!placedNodes.length" class="canvas-placeholder">
              <div style="font-size: 4rem;">👆</div>
              <p>{{ lang === 'zh' ? '拖拽左侧节点到此处构建流水线' : 'Drag nodes from the left to build pipeline' }}</p>
            </div>
            <div v-else style="display: flex; flex-wrap: wrap; gap: 1rem; padding: 1rem;">
              <div v-for="(n, i) in placedNodes" :key="i" class="placed-node">
                <div class="flow-node-icon">{{ n.icon }}</div>
                <div class="flow-node-title">{{ n.title }}</div>
              </div>
            </div>
          </div>
          <div class="canvas-footer">
            <span>{{ lang === 'zh' ? '节点数' : 'Nodes' }}: {{ placedNodes.length }}</span>
            <span>{{ lang === 'zh' ? '状态' : 'Status' }}: <span class="status-badge status-pending">{{ lang === 'zh' ? '未运行' : 'Not Run' }}</span></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useWorkflowStore } from '@/stores/workflowStore'
import { useThemeStore } from '@/stores/themeStore'
import { storeToRefs } from 'pinia'

const store = useWorkflowStore()
const { workflows } = storeToRefs(store)
const themeStore = useThemeStore()
const { language: lang } = storeToRefs(themeStore)

const workflowMode = ref<'smart' | 'manual'>('smart')
const activeDirection = ref('all')

const professionalDirections = [
  { id: 'writing', name: '写作', nameEn: 'Writing', icon: '✍️' },
  { id: 'coding', name: '编程', nameEn: 'Coding', icon: '💻' },
  { id: 'research', name: '研究', nameEn: 'Research', icon: '🔬' },
  { id: 'design', name: '设计', nameEn: 'Design', icon: '🎨' },
]

const workflowIcons: Record<string, string> = {
  content: '📝', image: '🖼️', data: '🔍', audio: '🎵', video: '🎬', custom: '🛠️'
}
const workflowStatusText: Record<string, string> = {
  success: '已启用', pending: '待配置', warning: '测试中'
}
workflows.value.forEach(w => {
  w.icon = workflowIcons[w.id] || '📄'
  w.statusText = workflowStatusText[w.status] || w.status
})

const filteredWorkflows = computed(() => {
  if (activeDirection.value === 'all') return workflows.value
  return workflows.value.filter(w => w.id.includes(activeDirection.value))
})

const nodeGroups = [
  {
    label: '📥 ' + (lang.value === 'zh' ? '输入节点' : 'Input Nodes'),
    nodes: [
      { id: 'input-text', icon: '📝', title: lang.value === 'zh' ? '文本输入' : 'Text Input' },
      { id: 'input-file', icon: '📁', title: lang.value === 'zh' ? '文件输入' : 'File Input' },
      { id: 'input-url', icon: '🔗', title: lang.value === 'zh' ? 'URL输入' : 'URL Input' },
    ]
  },
  {
    label: '🤖 ' + (lang.value === 'zh' ? 'AI处理节点' : 'AI Nodes'),
    nodes: [
      { id: 'ai-text', icon: '✏️', title: lang.value === 'zh' ? '文本生成' : 'Text Gen' },
      { id: 'ai-image', icon: '🖼️', title: lang.value === 'zh' ? '图像生成' : 'Image Gen' },
      { id: 'ai-audio', icon: '🎵', title: lang.value === 'zh' ? '音频生成' : 'Audio Gen' },
    ]
  },
  {
    label: '⚡ ' + (lang.value === 'zh' ? '技能节点' : 'Skill Nodes'),
    nodes: [
      { id: 'skill-code', icon: '💻', title: lang.value === 'zh' ? '代码执行' : 'Code Exec' },
      { id: 'skill-web', icon: '🌐', title: lang.value === 'zh' ? 'Web请求' : 'Web Req' },
      { id: 'skill-data', icon: '📊', title: lang.value === 'zh' ? '数据处理' : 'Data Proc' },
    ]
  },
  {
    label: '📤 ' + (lang.value === 'zh' ? '输出节点' : 'Output Nodes'),
    nodes: [
      { id: 'output-text', icon: '📄', title: lang.value === 'zh' ? '文本输出' : 'Text Out' },
      { id: 'output-file', icon: '💾', title: lang.value === 'zh' ? '文件输出' : 'File Out' },
    ]
  },
]

const placedNodes = ref<any[]>([])
let draggedId = ''

function dragNode(e: DragEvent, id: string) { draggedId = id }
function dropNode() {
  const group = nodeGroups.find(g => g.nodes.find(n => n.id === draggedId))
  const node = group?.nodes.find(n => n.id === draggedId)
  if (node) placedNodes.value.push({ ...node })
}
function loadWorkflow(id: string) { console.log('load', id) }
function createWorkflow() { }
function clearWorkflow() { placedNodes.value = [] }
function saveWorkflow() { }
function runWorkflow() { }
</script>

<style scoped>
.card { background: linear-gradient(145deg, var(--bg-card), rgba(15, 23, 42, 0.8)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }

.mode-toggle { display: flex; background: var(--bg-dark); border-radius: 8px; padding: 2px; }
.mode-toggle button { padding: 0.4rem 0.75rem; border-radius: 6px; border: none; background: transparent; cursor: pointer; font-size: 0.8rem; transition: all 0.3s; }
.mode-toggle button.active { background: var(--primary); color: white; }

.direction-filter { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
.dir-btn { padding: 0.3rem 0.75rem; border-radius: 20px; border: 1px solid var(--border); background: var(--bg-dark); cursor: pointer; transition: all 0.3s; font-size: 0.8rem; }
.dir-btn.active { background: var(--primary); color: white; border-color: var(--primary); }

.workflow-card {
  background: linear-gradient(145deg, var(--bg-card), rgba(15, 23, 42, 0.8));
  border-radius: 16px;
  padding: 1.75rem;
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.4s;
}
.workflow-card:hover { border-color: var(--primary); transform: translateY(-4px); box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15); }
.workflow-name { font-size: 1.1rem; font-weight: 600; }
.workflow-desc { color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem; }

.status-badge { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 500; }
.status-success { background: rgba(16, 185, 129, 0.2); color: var(--success); }
.status-pending { background: rgba(245, 158, 11, 0.2); color: var(--warning); }
.status-warning { background: rgba(245, 158, 11, 0.2); color: var(--warning); }

.node-panel { width: 220px; padding-right: 1rem; border-right: 1px solid var(--border); }
.node-group-label { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.75rem; margin-top: 1rem; }
.flow-node { background: var(--bg-card); border: 2px solid var(--border); border-radius: 10px; padding: 0.75rem; text-align: center; cursor: pointer; transition: all 0.3s; margin-bottom: 0.5rem; }
.flow-node:hover { border-color: var(--primary); }
.flow-node-icon { font-size: 1.5rem; }
.flow-node-title { font-size: 0.8rem; font-weight: 500; }

.canvas-area { background: var(--bg-dark); border-radius: 8px; min-height: 350px; }
.canvas-placeholder { text-align: center; color: var(--text-secondary); padding: 4rem; }
.placed-node { background: var(--bg-card); border: 2px solid var(--primary); border-radius: 10px; padding: 0.75rem; text-align: center; min-width: 100px; }
.canvas-footer { margin-top: 1rem; display: flex; justify-content: space-between; color: var(--text-secondary); font-size: 0.85rem; }
</style>