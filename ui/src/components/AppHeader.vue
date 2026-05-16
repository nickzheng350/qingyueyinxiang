<template>
  <header class="app-header">
    <div class="header-left">
      <button class="collapse-btn" @click="$emit('toggle-sidebar')">
        <span class="collapse-icon">{{ collapsed ? '→' : '←' }}</span>
      </button>
      <div class="breadcrumb">
        <span class="breadcrumb-item active">{{ currentModule }}</span>
      </div>
    </div>

    <div class="header-center">
      <nav class="header-tabs">
        <router-link
          v-for="tab in tabs"
          :key="tab.path"
          :to="tab.path"
          class="header-tab"
          active-class="active"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ lang === 'zh' ? tab.label : tab.labelEn }}</span>
        </router-link>
      </nav>
    </div>

    <div class="header-right">
      <!-- 主题切换组件 -->
      <ThemeSwitch />

      <!-- 语言切换 -->
      <button class="lang-btn" @click="toggleLanguage">
        {{ lang === 'zh' ? 'EN' : '中文' }}
      </button>

      <!-- 搜索 -->
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input
          type="text"
          class="search-input"
          :placeholder="lang === 'zh' ? '搜索...' : 'Search...'"
        />
      </div>

      <!-- 用户头像 -->
      <div class="user-avatar">
        {{ userInitial }}
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { storeToRefs } from 'pinia'
import ThemeSwitch from './ThemeSwitch.vue'

defineEmits(['toggle-sidebar'])

const route = useRoute()
const themeStore = useThemeStore()
const { language: lang } = storeToRefs(themeStore)

const collapsed = ref(false)

const tabs = [
  { path: '/dialogue', icon: '💬', label: '对话', labelEn: 'Chat' },
  { path: '/memory', icon: '🧠', label: '记忆', labelEn: 'Memory' },
  { path: '/skills', icon: '⚡', label: '技能', labelEn: 'Skills' },
  { path: '/plugins', icon: '🔌', label: '插件', labelEn: 'Plugins' },
  { path: '/workflow', icon: '🔄', label: '工作流', labelEn: 'Workflow' },
  { path: '/models', icon: '🤖', label: '模型', labelEn: 'Models' },
  { path: '/experience', icon: '📚', label: '经验库', labelEn: 'Experience' },
]

const currentModule = computed(() => {
  const path = route.path
  const map: Record<string, string> = {
    '/dialogue': '对话',
    '/memory': '记忆',
    '/skills': '技能',
    '/plugins': '插件',
    '/workflow': '工作流',
    '/models': '模型',
    '/experience': '经验库',
  }
  return map[path.split('/')[1]] || '清悦印象'
})

const userInitial = 'N'

function toggleLanguage() {
  themeStore.setLanguage(lang.value === 'zh' ? 'en' : 'zh')
}
</script>

<style scoped>
.app-header {
  position: fixed;
  top: 0;
  left: 280px;
  right: 0;
  height: 64px;
  background: var(--bg-card);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-lg);
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.collapse-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--bg-hover);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.collapse-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.breadcrumb-item {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.breadcrumb-item.active {
  color: var(--text-primary);
  font-weight: 600;
}

.header-center {
  display: flex;
  align-items: center;
}

.header-tabs {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 4px;
}

.header-tab {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.8rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.header-tab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.header-tab.active {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
}

.tab-icon {
  font-size: 0.9rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.lang-btn {
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.lang-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--primary);
}

.search-box {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-xs) var(--space-md);
}

.search-icon {
  font-size: 0.875rem;
  opacity: 0.6;
}

.search-input {
  background: none;
  border: none;
  color: var(--text-primary);
  font-size: 0.875rem;
  outline: none;
  width: 140px;
}

.search-input::placeholder {
  color: var(--text-muted);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--secondary), var(--accent));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.user-avatar:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-md);
}
</style>
