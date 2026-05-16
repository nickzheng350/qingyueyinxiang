<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">📚 {{ lang === 'zh' ? '经验库' : 'Experience Library' }}</div>
        <div class="card-subtitle">{{ lang === 'zh' ? '管理和复用AI学习经验' : 'Manage and reuse AI learning experiences' }}</div>
      </div>
      <div style="display: flex; gap: 0.5rem;">
        <button class="btn btn-primary" @click="generateFromDialogue">⚡ {{ lang === 'zh' ? '从对话生成' : 'Generate from Dialogue' }}</button>
        <button class="btn btn-secondary" @click="fetchExperiences">🔄 {{ lang === 'zh' ? '刷新' : 'Refresh' }}</button>
      </div>
    </div>

    <!-- 专业方向筛选 -->
    <div class="direction-section">
      <div class="direction-tabs">
        <button
          class="direction-tab"
          :class="{ active: activeDirection === 'all' }"
          @click="activeDirection = 'all'"
        >
          🌐 {{ lang === 'zh' ? '全部' : 'All' }}
        </button>
        <button
          v-for="dir in professionalDirections"
          :key="dir.id"
          class="direction-tab"
          :class="{ active: activeDirection === dir.id }"
          @click="activeDirection = dir.id"
        >
          {{ dir.icon }} {{ lang === 'zh' ? dir.name : dir.nameEn }}
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📚</div>
        <div class="stat-info">
          <div class="stat-num">{{ experiences.length }}</div>
          <div class="stat-label">{{ lang === 'zh' ? '经验总数' : 'Total Experiences' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📈</div>
        <div class="stat-info">
          <div class="stat-num">{{ totalUsage }}</div>
          <div class="stat-label">{{ lang === 'zh' ? '总使用次数' : 'Total Usage' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⭐</div>
        <div class="stat-info">
          <div class="stat-num">{{ avgQuality }}</div>
          <div class="stat-label">{{ lang === 'zh' ? '平均质量分' : 'Avg Quality' }}</div>
        </div>
      </div>
    </div>

    <!-- 智能整合建议 -->
    <div class="suggestions-section">
      <h3 class="section-title">💡 {{ lang === 'zh' ? '智能整合建议' : 'Smart Integration Suggestions' }}</h3>
      <div class="suggestions-list">
        <div v-for="suggestion in suggestions" :key="suggestion.id || suggestion.message" class="suggestion-card">
          <div class="suggestion-icon">{{ suggestion.type === 'merge' ? '🔀' : '✨' }}</div>
          <div class="suggestion-content">
            <div class="suggestion-type">{{ getSuggestionTypeText(suggestion.type) }}</div>
            <div class="suggestion-message">{{ suggestion.message }}</div>
          </div>
          <button class="btn btn-primary btn-sm" @click="applySuggestion(suggestion)">
            {{ lang === 'zh' ? '应用' : 'Apply' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 经验列表 -->
    <div class="experience-list">
      <h3 class="section-title">🎯 {{ lang === 'zh' ? '经验列表' : 'Experience List' }}</h3>
      <div v-if="loading" class="loading-state">{{ lang === 'zh' ? '加载中...' : 'Loading...' }}</div>
      <div v-else class="experience-grid">
        <div v-for="exp in filteredExperiences" :key="exp.id" class="experience-card">
          <div class="exp-header">
            <div class="exp-direction">
              {{ getDirectionIcon(exp.professionalDirection) }}
              {{ getDirectionName(exp.professionalDirection) }}
            </div>
            <div class="exp-quality">
              <span class="quality-bar">
                <span class="quality-fill" :style="{ width: exp.quality + '%' }"></span>
              </span>
              <span class="quality-num">{{ exp.quality }}%</span>
            </div>
          </div>

          <div class="exp-name">{{ exp.name }}</div>
          <div class="exp-description">{{ exp.description }}</div>

          <div class="exp-tags">
            <span v-for="tag in exp.tags" :key="tag" class="exp-tag">{{ tag }}</span>
          </div>

          <div class="exp-footer">
            <span class="exp-source" v-if="exp.sourceDialogue">
              💬 {{ exp.sourceDialogue }}
            </span>
            <span class="exp-usage">
              📊 {{ exp.usageCount }} {{ lang === 'zh' ? '次使用' : 'uses' }}
            </span>
          </div>

          <div class="exp-actions">
            <button class="btn btn-secondary btn-sm" @click="useExperience(exp)">
              {{ lang === 'zh' ? '使用' : 'Use' }}
            </button>
            <button class="btn btn-secondary btn-sm" @click="duplicateExperience(exp)">
              {{ lang === 'zh' ? '复制' : 'Copy' }}
            </button>
            <button class="btn btn-danger btn-sm" @click="deleteExperience(exp.id)">
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 从对话生成对话框 -->
    <div v-if="showGenerateDialog" class="dialog-overlay" @click.self="showGenerateDialog = false">
      <div class="dialog">
        <h3>{{ lang === 'zh' ? '从对话生成经验' : 'Generate Experience from Dialogue' }}</h3>
        <div class="form-group">
          <label>{{ lang === 'zh' ? '选择对话' : 'Select Dialogue' }}</label>
          <select v-model="selectedDialogueId">
            <option value="">{{ lang === 'zh' ? '请选择' : 'Please select' }}</option>
            <option v-for="d in dialogues" :key="d.id" :value="d.id">
              {{ d.title }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>{{ lang === 'zh' ? '专业方向' : 'Professional Direction' }}</label>
          <select v-model="newExpDirection">
            <option v-for="dir in professionalDirections" :key="dir.id" :value="dir.id">
              {{ dir.icon }} {{ lang === 'zh' ? dir.name : dir.nameEn }}
            </option>
          </select>
        </div>
        <div class="dialog-actions">
          <button class="btn btn-secondary" @click="showGenerateDialog = false">{{ lang === 'zh' ? '取消' : 'Cancel' }}</button>
          <button class="btn btn-primary" @click="confirmGenerate" :class="{ 'btn-loading': generating }">
            {{ lang === 'zh' ? '生成' : 'Generate' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useExperienceStore } from '@/stores/experienceStore'
import { useDialogueStore } from '@/stores/dialogueStore'
import { useThemeStore } from '@/stores/theme'
import { storeToRefs } from 'pinia'

const experienceStore = useExperienceStore()
const dialogueStore = useDialogueStore()
const themeStore = useThemeStore()
const { experiences, loading, activeDirection, professionalDirections } = storeToRefs(experienceStore)
const { dialogues } = storeToRefs(dialogueStore)
const { language: lang } = storeToRefs(themeStore)

const suggestions = ref<any[]>([])
const showGenerateDialog = ref(false)
const selectedDialogueId = ref('')
const newExpDirection = ref('coding')
const generating = ref(false)

const filteredExperiences = computed(() => {
  return experienceStore.getExperiencesByDirection(activeDirection.value)
})

const totalUsage = computed(() => experiences.value.reduce((sum, e) => sum + e.usageCount, 0))
const avgQuality = computed(() => {
  if (!experiences.value.length) return 0
  return Math.round(experiences.value.reduce((sum, e) => sum + e.quality, 0) / experiences.value.length)
})

function getDirectionIcon(direction: string) {
  const dir = professionalDirections.value.find(d => d.id === direction)
  return dir?.icon || '🌐'
}

function getDirectionName(direction: string) {
  const dir = professionalDirections.value.find(d => d.id === direction)
  if (!dir) return direction
  return lang.value === 'zh' ? dir.name : dir.nameEn
}

function getSuggestionTypeText(type: string) {
  const texts: Record<string, string> = {
    merge: lang.value === 'zh' ? '合并建议' : 'Merge Suggestion',
    optimize: lang.value === 'zh' ? '优化建议' : 'Optimization',
    split: lang.value === 'zh' ? '拆分建议' : 'Split Suggestion',
  }
  return texts[type] || type
}

function fetchExperiences() {
  experienceStore.fetchExperiences()
  loadSuggestions()
}

async function loadSuggestions() {
  suggestions.value = await experienceStore.getSuggestions()
}

function generateFromDialogue() {
  showGenerateDialog.value = true
}

async function confirmGenerate() {
  if (!selectedDialogueId.value) return
  generating.value = true
  await experienceStore.generateFromDialogue(selectedDialogueId.value)
  generating.value = false
  showGenerateDialog.value = false
}

function applySuggestion(suggestion: any) {
  console.log('Apply suggestion:', suggestion)
  // 实现建议应用逻辑
}

function useExperience(exp: any) {
  console.log('Use experience:', exp)
  exp.usageCount++
}

function duplicateExperience(exp: any) {
  experienceStore.addExperience({
    name: exp.name + ' (Copy)',
    description: exp.description,
    professionalDirection: exp.professionalDirection,
    tags: [...exp.tags],
    quality: exp.quality,
  })
}

function deleteExperience(id: string) {
  experienceStore.deleteExperience(id)
}

onMounted(() => {
  fetchExperiences()
  dialogueStore.fetchDialogues()
})
</script>

<style scoped>
.card { background: linear-gradient(145deg, var(--bg-card), var(--bg-dark)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }

.direction-section { margin-bottom: 1.5rem; }
.direction-tabs { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.direction-tab { padding: 0.5rem 1rem; border-radius: 20px; border: 1px solid var(--border); background: var(--bg-dark); cursor: pointer; transition: all 0.3s; font-size: 0.85rem; }
.direction-tab:hover { border-color: var(--primary); }
.direction-tab.active { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; border-color: transparent; }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.stat-card { background: var(--bg-dark); border-radius: 12px; padding: 1rem; display: flex; align-items: center; gap: 1rem; }
.stat-icon { font-size: 2rem; }
.stat-num { font-size: 1.5rem; font-weight: bold; }
.stat-label { font-size: 0.8rem; color: var(--text-secondary); }

.section-title { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; }

.suggestions-section { margin-bottom: 2rem; }
.suggestions-list { display: flex; flex-direction: column; gap: 0.75rem; }
.suggestion-card { background: var(--bg-dark); border-radius: 12px; padding: 1rem; display: flex; align-items: center; gap: 1rem; border-left: 3px solid var(--warning); }
.suggestion-icon { font-size: 1.5rem; }
.suggestion-content { flex: 1; }
.suggestion-type { font-size: 0.75rem; color: var(--warning); font-weight: 500; }
.suggestion-message { font-size: 0.85rem; color: var(--text-secondary); }

.experience-list {}
.experience-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 1.5rem; }
.experience-card { background: var(--bg-dark); border-radius: 12px; padding: 1.25rem; transition: all 0.3s; }
.experience-card:hover { border: 1px solid var(--primary); transform: translateY(-2px); }
.exp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.exp-direction { font-size: 0.75rem; color: white; }
.exp-quality { display: flex; align-items: center; gap: 0.5rem; }
.quality-bar { width: 60px; height: 6px; background: var(--bg-card); border-radius: 3px; overflow: hidden; }
.quality-fill { height: 100%; background: linear-gradient(90deg, var(--success), var(--primary)); border-radius: 3px; }
.quality-num { font-size: 0.75rem; color: var(--success); font-weight: 600; }
.exp-name { font-weight: 600; margin-bottom: 0.5rem; }
.exp-description { color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.75rem; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.exp-tags { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
.exp-tag { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; background: color-mix(in srgb, var(--primary) 20%, transparent); color: white; }
.exp-footer { display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
.exp-source { opacity: 0.7; }
.exp-actions { display: flex; gap: 0.5rem; }

.loading-state { text-align: center; padding: 2rem; color: var(--text-secondary); }

.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.dialog { background: var(--bg-card); border-radius: 16px; padding: 2rem; width: 500px; max-width: 90%; }
.dialog h3 { margin-bottom: 1.5rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--text-secondary); }
.form-group select, .form-group input { width: 100%; background: var(--bg-dark); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; color: var(--text-primary); outline: none; }
.form-group select:focus, .form-group input:focus { border-color: var(--primary); }
.dialog-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem; }
</style>
