<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">🧠 {{ lang === 'zh' ? '记忆中心' : 'Memory Center' }}</div>
        <div class="card-subtitle">{{ lang === 'zh' ? '管理知识库和学习经验' : 'Manage knowledge base and learning experiences' }}</div>
      </div>
      <div style="display: flex; gap: 0.5rem;">
        <el-button type="primary" @click="showAddDialog = true">➕ {{ lang === 'zh' ? '添加记忆' : 'Add Memory' }}</el-button>
        <el-button @click="fetchEntries">🔄 {{ lang === 'zh' ? '刷新' : 'Refresh' }}</el-button>
      </div>
    </div>

    <!-- 专业方向选择 -->
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

    <!-- 搜索栏 -->
    <div class="search-section">
      <div class="search-box">
        <span>🔍</span>
        <input
          type="text"
          v-model="searchKeyword"
          :placeholder="lang === 'zh' ? '搜索记忆...' : 'Search memories...'"
          @input="handleSearch"
        />
      </div>
      <div class="filter-tags">
        <span
          v-for="tag in tags.slice(0, 5)"
          :key="tag"
          class="filter-tag"
          :class="{ active: selectedTags.includes(tag) }"
          @click="toggleTag(tag)"
        >
          {{ tag }}
        </span>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📚</div>
        <div class="stat-info">
          <div class="stat-num">{{ entries.length }}</div>
          <div class="stat-label">{{ lang === 'zh' ? '记忆总数' : 'Total Memories' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🏷️</div>
        <div class="stat-info">
          <div class="stat-num">{{ tags.length }}</div>
          <div class="stat-label">{{ lang === 'zh' ? '标签数' : 'Tags' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📂</div>
        <div class="stat-info">
          <div class="stat-num">{{ categories.length }}</div>
          <div class="stat-label">{{ lang === 'zh' ? '分类数' : 'Categories' }}</div>
        </div>
      </div>
    </div>

    <!-- 知识库分类 -->
    <div class="category-section">
      <h3 class="section-title">📂 {{ lang === 'zh' ? '知识分类' : 'Knowledge Categories' }}</h3>
      <div class="category-grid">
        <div v-for="cat in categories" :key="cat.id" class="category-card">
          <div class="cat-icon">{{ getCategoryIcon(cat.type) }}</div>
          <div class="cat-info">
            <div class="cat-name">{{ cat.name }}</div>
            <div class="cat-count">{{ cat.count }} {{ lang === 'zh' ? '条记忆' : 'entries' }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 记忆列表 -->
    <div class="memory-list">
      <h3 class="section-title">💭 {{ lang === 'zh' ? '记忆列表' : 'Memory List' }}</h3>
      <div v-if="loading" class="loading-state">{{ lang === 'zh' ? '加载中...' : 'Loading...' }}</div>
      <div v-else class="memory-grid">
        <div v-for="entry in filteredEntries" :key="entry.id" class="memory-card">
          <div class="memory-header">
            <div class="memory-direction">
              {{ getDirectionIcon(entry.professionalDirection) }}
              {{ getDirectionName(entry.professionalDirection) }}
            </div>
            <button class="delete-btn" @click="deleteEntry(entry.id)">🗑️</button>
          </div>
          <div class="memory-title">{{ entry.title }}</div>
          <div class="memory-content">{{ entry.content }}</div>
          <div class="memory-tags">
            <span v-for="tag in entry.tags" :key="tag" class="memory-tag">{{ tag }}</span>
          </div>
          <div class="memory-footer">
            <span class="memory-source" v-if="entry.source">📎 {{ entry.source }}</span>
            <span class="memory-time">{{ formatTime(entry.updatedAt) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加记忆对话框 -->
    <div v-if="showAddDialog" class="dialog-overlay" @click.self="showAddDialog = false">
      <div class="dialog">
        <h3>{{ lang === 'zh' ? '添加新记忆' : 'Add New Memory' }}</h3>
        <div class="form-group">
          <label>{{ lang === 'zh' ? '标题' : 'Title' }}</label>
          <input v-model="newEntry.title" type="text" />
        </div>
        <div class="form-group">
          <label>{{ lang === 'zh' ? '内容' : 'Content' }}</label>
          <textarea v-model="newEntry.content" rows="4"></textarea>
        </div>
        <div class="form-group">
          <label>{{ lang === 'zh' ? '专业方向' : 'Direction' }}</label>
          <select v-model="newEntry.professionalDirection">
            <option v-for="dir in professionalDirections" :key="dir.id" :value="dir.id">
              {{ dir.icon }} {{ lang === 'zh' ? dir.name : dir.nameEn }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>{{ lang === 'zh' ? '标签 (逗号分隔)' : 'Tags (comma separated)' }}</label>
          <input v-model="newEntry.tagsInput" type="text" />
        </div>
        <div class="dialog-actions">
          <el-button @click="showAddDialog = false">{{ lang === 'zh' ? '取消' : 'Cancel' }}</el-button>
          <el-button type="primary" @click="addNewEntry">{{ lang === 'zh' ? '保存' : 'Save' }}</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMemoryStore } from '@/stores/memoryStore'
import { useThemeStore } from '@/stores/themeStore'
import { storeToRefs } from 'pinia'

const memoryStore = useMemoryStore()
const themeStore = useThemeStore()
const { entries, categories, tags, loading, activeDirection } = storeToRefs(memoryStore)
const { language: lang } = storeToRefs(themeStore)
const { professionalDirections } = storeToRefs(memoryStore)

const searchKeyword = ref('')
const selectedTags = ref<string[]>([])
const showAddDialog = ref(false)
const newEntry = ref({
  title: '',
  content: '',
  professionalDirection: 'coding',
  tagsInput: '',
})

const filteredEntries = computed(() => {
  let result = memoryStore.getEntriesByDirection(activeDirection.value)
  if (searchKeyword.value) {
    result = memoryStore.searchEntries(searchKeyword.value)
  }
  if (selectedTags.value.length > 0) {
    result = result.filter(e => e.tags.some(t => selectedTags.value.includes(t)))
  }
  return result
})

function handleSearch() {
  // 搜索会在computed中自动处理
}

function toggleTag(tag: string) {
  const idx = selectedTags.value.indexOf(tag)
  if (idx === -1) {
    selectedTags.value.push(tag)
  } else {
    selectedTags.value.splice(idx, 1)
  }
}

function getCategoryIcon(type: string) {
  const icons: Record<string, string> = { coding: '💻', writing: '✍️', research: '🔬', design: '🎨' }
  return icons[type] || '📁'
}

function getDirectionIcon(direction?: string) {
  const dir = professionalDirections.value.find(d => d.id === direction)
  return dir?.icon || '🌐'
}

function getDirectionName(direction?: string) {
  if (!direction) return lang.value === 'zh' ? '全部' : 'All'
  const dir = professionalDirections.value.find(d => d.id === direction)
  if (!dir) return direction
  return lang.value === 'zh' ? dir.name : dir.nameEn
}

function formatTime(time: string) {
  return new Date(time).toLocaleDateString()
}

function addNewEntry() {
  memoryStore.addEntry({
    title: newEntry.value.title,
    content: newEntry.value.content,
    professionalDirection: newEntry.value.professionalDirection,
    tags: newEntry.value.tagsInput.split(',').map(t => t.trim()).filter(Boolean),
  })
  showAddDialog.value = false
  newEntry.value = { title: '', content: '', professionalDirection: 'coding', tagsInput: '' }
}

function deleteEntry(id: string) {
  memoryStore.deleteEntry(id)
}

function fetchEntries() {
  memoryStore.fetchEntries()
}

onMounted(() => {
  memoryStore.fetchEntries()
})
</script>

<style scoped>
.card { background: linear-gradient(145deg, var(--bg-card), rgba(15, 23, 42, 0.8)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }

.direction-section { margin-bottom: 1.5rem; }
.direction-tabs { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.direction-tab { padding: 0.5rem 1rem; border-radius: 20px; border: 1px solid var(--border); background: var(--bg-dark); cursor: pointer; transition: all 0.3s; font-size: 0.85rem; }
.direction-tab:hover { border-color: var(--primary); }
.direction-tab.active { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; border-color: transparent; }

.search-section { margin-bottom: 1.5rem; }
.search-box { display: flex; align-items: center; gap: 0.5rem; background: var(--bg-dark); border: 1px solid var(--border); border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.75rem; }
.search-box input { flex: 1; background: transparent; border: none; color: var(--text-primary); outline: none; }

.filter-tags { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.filter-tag { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; background: var(--bg-dark); border: 1px solid var(--border); cursor: pointer; transition: all 0.3s; }
.filter-tag.active { background: var(--primary); color: white; border-color: var(--primary); }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.stat-card { background: var(--bg-dark); border-radius: 12px; padding: 1rem; display: flex; align-items: center; gap: 1rem; }
.stat-icon { font-size: 2rem; }
.stat-num { font-size: 1.5rem; font-weight: bold; }
.stat-label { font-size: 0.8rem; color: var(--text-secondary); }

.section-title { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; }

.category-section { margin-bottom: 2rem; }
.category-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
.category-card { background: var(--bg-dark); border-radius: 12px; padding: 1rem; display: flex; align-items: center; gap: 1rem; cursor: pointer; transition: all 0.3s; }
.category-card:hover { border: 1px solid var(--primary); }
.cat-icon { font-size: 1.5rem; }
.cat-name { font-weight: 500; }
.cat-count { font-size: 0.8rem; color: var(--text-secondary); }

.memory-list { margin-bottom: 2rem; }
.memory-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1.5rem; }
.memory-card { background: var(--bg-dark); border-radius: 12px; padding: 1.25rem; transition: all 0.3s; }
.memory-card:hover { border: 1px solid var(--primary); transform: translateY(-2px); }
.memory-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.memory-direction { font-size: 0.75rem; color: var(--primary); }
.delete-btn { background: none; border: none; cursor: pointer; opacity: 0; transition: opacity 0.3s; }
.memory-card:hover .delete-btn { opacity: 1; }
.memory-title { font-weight: 600; margin-bottom: 0.5rem; }
.memory-content { color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.75rem; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.memory-tags { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
.memory-tag { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; background: rgba(99, 102, 241, 0.2); color: var(--primary); }
.memory-footer { display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-secondary); }
.memory-source { opacity: 0.7; }

.loading-state { text-align: center; padding: 2rem; color: var(--text-secondary); }

.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.dialog { background: var(--bg-card); border-radius: 16px; padding: 2rem; width: 500px; max-width: 90%; }
.dialog h3 { margin-bottom: 1.5rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--text-secondary); }
.form-group input, .form-group textarea, .form-group select { width: 100%; background: var(--bg-dark); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; color: var(--text-primary); outline: none; }
.form-group input:focus, .form-group textarea:focus, .form-group select:focus { border-color: var(--primary); }
.dialog-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem; }
</style>
