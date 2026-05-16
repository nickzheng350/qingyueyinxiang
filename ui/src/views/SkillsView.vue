<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">⚡ {{ lang === 'zh' ? '技能中心' : 'Skills Center' }}</div>
        <div class="card-subtitle">{{ lang === 'zh' ? '管理已安装的技能' : 'Manage installed skills' }}</div>
      </div>
      <div style="display: flex; gap: 0.5rem;">
        <button class="btn btn-primary" @click="$router.push('/market')">🏪 {{ lang === 'zh' ? '技能市场' : 'Market' }}</button>
        <button class="btn btn-secondary" @click="fetchInstalled">🔄 {{ lang === 'zh' ? '刷新' : 'Refresh' }}</button>
      </div>
    </div>

    <!-- Tab切换：已安装/市场 -->
    <div class="skill-tabs">
      <button class="skill-tab" :class="{ active: activeTab === 'installed' }" @click="activeTab = 'installed'">
        📦 {{ lang === 'zh' ? '已安装' : 'Installed' }} ({{ installed.length }})
      </button>
      <button class="skill-tab" :class="{ active: activeTab === 'market' }" @click="activeTab = 'market'">
        🏪 {{ lang === 'zh' ? '技能市场' : 'Market' }} ({{ market.length }})
      </button>
    </div>

    <!-- 专业方向筛选 -->
    <div class="direction-filter">
      <button
        v-for="dir in professionalDirections"
        :key="dir.id"
        class="dir-btn"
        :class="{ active: activeDirection === dir.id }"
        @click="activeDirection = activeDirection === dir.id ? 'all' : dir.id"
      >
        {{ dir.icon }} {{ lang === 'zh' ? dir.name : dir.nameEn }}
      </button>
    </div>

    <!-- 统计 -->
    <div class="skill-stats">
      <div><div class="stat-num">{{ installed.length }}</div><div class="stat-label">{{ lang === 'zh' ? '已安装' : 'Installed' }}</div></div>
      <div><div class="stat-num">{{ enabledCount }}</div><div class="stat-label">{{ lang === 'zh' ? '已启用' : 'Enabled' }}</div></div>
      <div><div class="stat-num">{{ disabledCount }}</div><div class="stat-label">{{ lang === 'zh' ? '已禁用' : 'Disabled' }}</div></div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">⏳ {{ lang === 'zh' ? '加载中...' : 'Loading...' }}</div>

    <!-- 已安装技能列表 -->
    <div v-else-if="activeTab === 'installed'" class="grid-auto">
      <SkillCard
        v-for="s in filteredInstalled"
        :key="s.id"
        :skill="s"
        :show-toggle="true"
        @toggle="toggleSkill(s)"
      />
    </div>

    <!-- 市场技能列表 -->
    <div v-else class="grid-auto">
      <SkillCard
        v-for="s in filteredMarket"
        :key="s.id"
        :skill="s"
        :show-install="true"
        @install="installSkill(s)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import SkillCard from '@/components/SkillCard.vue'
import { useSkillStore } from '@/stores/skillStore'
import { useThemeStore } from '@/stores/theme'
import { storeToRefs } from 'pinia'
import { client } from '@/api/client'

const store = useSkillStore()
const themeStore = useThemeStore()
const { installed, market, loading } = storeToRefs(store)
const { language: lang } = storeToRefs(themeStore)

const activeTab = ref<'installed' | 'market'>('installed')
const activeDirection = ref('all')

const professionalDirections = [
  { id: 'code', name: '编程', nameEn: 'Coding', icon: '💻' },
  { id: 'web', name: '网页', nameEn: 'Web', icon: '🌐' },
  { id: 'ai', name: 'AI', nameEn: 'AI', icon: '🤖' },
  { id: 'system', name: '系统', nameEn: 'System', icon: '⚙️' },
  { id: 'video', name: '视频剪辑', nameEn: 'Video Editing', icon: '🎬' },
  { id: 'audio', name: '音频剪辑', nameEn: 'Audio Editing', icon: '🎵' },
]

const mockInstalled = [
  { id: 's1', name: '代码执行', nameEn: 'Code Execution', description: '安全执行Python/JS代码片段', type: 'code', enabled: true, installed: true },
  { id: 's2', name: '文件处理', nameEn: 'File Processing', description: '文件的读取、写入、压缩、解压', type: 'system', enabled: true, installed: true },
  { id: 's3', name: '网页搜索', nameEn: 'Web Search', description: '搜索互联网内容', type: 'web', enabled: true, installed: true },
  { id: 's4', name: '图像处理', nameEn: 'Image Processing', description: '图像识别、生成、编辑', type: 'ai', enabled: false, installed: true },
  { id: 's5', name: '视频剪辑', nameEn: 'Video Editing', description: '视频剪辑、转场、特效、字幕', type: 'video', enabled: true, installed: true },
  { id: 's6', name: '音频剪辑', nameEn: 'Audio Editing', description: '音频剪辑、降噪、混音、格式转换', type: 'audio', enabled: true, installed: true },
]

const mockMarket = [
  { id: 'sm1', name: '数据可视化', nameEn: 'Data Visualization', description: '生成交互式图表和数据看板', type: 'code', enabled: false, installed: false },
  { id: 'sm2', name: '视频处理', nameEn: 'Video Processing', description: '视频剪辑、转码、特效处理', type: 'video', enabled: false, installed: false },
  { id: 'sm3', name: 'PDF处理', nameEn: 'PDF Processing', description: 'PDF解析、编辑、合并、分割', type: 'system', enabled: false, installed: false },
  { id: 'sm4', name: '语音合成', nameEn: 'Text-to-Speech', description: '文本转语音，支持多种音色', type: 'ai', enabled: false, installed: false },
  { id: 'sm5', name: '音频处理', nameEn: 'Audio Processing', description: '音频剪辑、降噪、混音', type: 'audio', enabled: false, installed: false },
  { id: 'sm6', name: '视频生成', nameEn: 'Video Generation', description: 'AI视频生成和动画制作', type: 'video', enabled: false, installed: false },
]

const filteredInstalled = computed(() => {
  if (activeDirection.value === 'all') return installed.value
  return installed.value.filter(s => s.type === activeDirection.value)
})

const filteredMarket = computed(() => {
  if (activeDirection.value === 'all') return market.value
  return market.value.filter(s => s.type === activeDirection.value)
})

const enabledCount = computed(() => installed.value.filter(s => s.enabled).length)
const disabledCount = computed(() => installed.value.filter(s => !s.enabled).length)

async function fetchInstalled() {
  await store.fetchInstalled()
  if (!installed.value.length) installed.value = mockInstalled
}

async function fetchMarket() {
  await store.fetchMarket()
  if (!market.value.length) market.value = mockMarket
}

function toggleSkill(skill: any) {
  skill.enabled = !skill.enabled
}

async function installSkill(skill: any) {
  try {
    // 调用后端安装接口
    const response = await client.post(`/skills/${skill.id}/install`)
    
    if (response.status === 'success') {
      skill.installed = true
      installed.value.push({ 
        ...skill, 
        enabled: false,
        installed: true 
      })
      ElMessage.success(response.message || `${skill.name} 安装成功`)
    } else {
      ElMessage.error(response.message || `${skill.name} 安装失败`)
    }
  } catch (error: any) {
    ElMessage.error(error.message || `${skill.name} 安装失败`)
  }
}

onMounted(() => {
  fetchInstalled()
  fetchMarket()
})
</script>

<style scoped>
.card { background: linear-gradient(145deg, var(--bg-card), var(--bg-dark)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }

.skill-tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.skill-tab { padding: 0.5rem 1.25rem; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-dark); cursor: pointer; transition: all 0.3s; color: white; }
.skill-tab:hover { border-color: var(--primary); }
.skill-tab.active { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; border-color: transparent; }

.direction-filter { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.dir-btn { padding: 0.3rem 0.75rem; border-radius: 20px; border: 1px solid var(--border); background: var(--bg-dark); cursor: pointer; transition: all 0.3s; font-size: 0.8rem; color: white; }
.dir-btn:hover { border-color: var(--primary); }
.dir-btn.active { background: var(--primary); color: white; border-color: var(--primary); }

.skill-stats { display: flex; gap: 2rem; margin-bottom: 1.5rem; padding: 1rem; background: var(--bg-dark); border-radius: 8px; }
.stat-num { font-size: 1.5rem; font-weight: bold; }
.stat-label { font-size: 0.85rem; color: var(--text-secondary); }
.grid-auto { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
.loading-state { text-align: center; padding: 3rem; color: var(--text-secondary); }
</style>