<template>
  <header class="top-bar">
    <!-- 顶部Tab导航 -->
    <div class="top-tabs">
      <router-link
        v-for="tab in topTabs"
        :key="tab.path"
        :to="tab.path"
        class="top-tab"
        active-class="active"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ lang === 'zh' ? tab.label : tab.labelEn }}</span>
      </router-link>
    </div>

    <!-- 右侧操作区 -->
    <div class="top-actions">
      <!-- 主题切换 -->
      <div class="theme-switcher">
        <button
          v-for="theme in themeList"
          :key="theme.name"
          class="theme-btn"
          :class="{ active: currentTheme === theme.name }"
          :style="{ background: theme.primary }"
          :title="theme.nameZh"
          @click="setTheme(theme.name)"
        ></button>
      </div>

      <!-- 语言切换 -->
      <button class="lang-btn" @click="toggleLanguage">
        {{ lang === 'zh' ? 'EN' : '中' }}
      </button>

      <!-- 搜索框 -->
      <div class="search-box">
        <span>🔍</span>
        <input
          type="text"
          :placeholder="lang === 'zh' ? '搜索...' : 'Search...'"
          v-model="keyword"
          @keyup.enter="handleSearch"
        />
      </div>

      <!-- 用户头像 -->
      <div class="user-avatar">N</div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore, themes, type ThemeName } from '@/stores/theme'
import { storeToRefs } from 'pinia'

const route = useRoute()
const themeStore = useThemeStore()
const { language: lang, currentTheme } = storeToRefs(themeStore)

const keyword = ref('')

const topTabs = [
  { path: '/dialogue', icon: '💬', label: '对话', labelEn: 'Chat' },
  { path: '/memory', icon: '🧠', label: '记忆', labelEn: 'Memory' },
  { path: '/skills', icon: '⚡', label: '技能', labelEn: 'Skills' },
  { path: '/plugins', icon: '🔌', label: '插件', labelEn: 'Plugins' },
  { path: '/workflow', icon: '🔄', label: '工作流', labelEn: 'Workflow' },
  { path: '/models', icon: '🤖', label: '模型', labelEn: 'Models' },
  { path: '/experience', icon: '📚', label: '经验库', labelEn: 'Experience' },
]

const themeList = Object.values(themes)

function setTheme(name: ThemeName) {
  themeStore.setTheme(name)
}

function toggleLanguage() {
  themeStore.setLanguage(lang.value === 'zh' ? 'en' : 'zh')
}

function handleSearch() {
  console.log('search:', keyword.value)
}
</script>

<style scoped>
.top-bar {
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.98) 0%, rgba(15, 23, 42, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  padding: 0.75rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

.top-tabs {
  display: flex;
  gap: 0.25rem;
}

.top-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.3s;
  font-size: 0.9rem;
}

.top-tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.top-tab.active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(139, 92, 246, 0.15));
  color: var(--text-primary);
}

.tab-icon {
  font-size: 1.1rem;
}

.tab-label {
  font-weight: 500;
}

.top-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.theme-switcher {
  display: flex;
  gap: 0.35rem;
}

.theme-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.3s;
}

.theme-btn:hover {
  transform: scale(1.15);
}

.theme-btn.active {
  border-color: white;
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

.lang-btn {
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-dark);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  transition: all 0.3s;
}

.lang-btn:hover {
  border-color: var(--primary);
}

.search-box {
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
}

.search-box input {
  background: transparent;
  border: none;
  color: var(--text-primary);
  outline: none;
  width: 140px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-weight: 600;
}

@media (max-width: 1200px) {
  .tab-label {
    display: none;
  }
  .top-tab {
    padding: 0.625rem 0.75rem;
  }
}
</style>
