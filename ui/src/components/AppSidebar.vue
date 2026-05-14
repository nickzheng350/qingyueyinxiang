<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-logo">H</div>
      <div>
        <div class="sidebar-title">清悦印象</div>
        <div class="sidebar-subtitle">清新淡雅，悦己，留下印象<</div>
      </div>
    </div>

    <!-- 主导航 -->
    <nav class="nav-menu">
      <div class="nav-section-title">{{ lang === 'zh' ? '主导航' : 'Main' }}</div>
      <li v-for="item in mainNav" :key="item.path" class="nav-item">
        <router-link :to="item.path" active-class="active">
          <span class="nav-icon">{{ item.icon }}</span>
          {{ lang === 'zh' ? item.label : item.labelEn }}
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
        </router-link>
      </li>
    </nav>

    <!-- 当前模块子菜单 -->
    <nav v-if="currentSubMenu.length" class="nav-menu sub-menu">
      <div class="nav-section-title">{{ lang === 'zh' ? '当前模块' : 'Current Module' }}</div>
      <li v-for="item in currentSubMenu" :key="item.path" class="nav-item">
        <router-link :to="item.path" active-class="active">
          <span class="nav-icon">{{ item.icon }}</span>
          {{ lang === 'zh' ? item.label : item.labelEn }}
        </router-link>
      </li>
    </nav>

    <!-- 设置导航 -->
    <nav class="nav-menu settings-menu">
      <div class="nav-section-title">{{ lang === 'zh' ? '设置' : 'Settings' }}</div>
      <li v-for="item in settingsNav" :key="item.path" class="nav-item">
        <router-link :to="item.path" active-class="active">
          <span class="nav-icon">{{ item.icon }}</span>
          {{ lang === 'zh' ? item.label : item.labelEn }}
        </router-link>
      </li>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { storeToRefs } from 'pinia'

const route = useRoute()
const themeStore = useThemeStore()
const { language: lang } = storeToRefs(themeStore)

const mainNav = [
  { path: '/dialogue', icon: '💬', label: '对话', labelEn: 'Chat' },
  { path: '/memory', icon: '🧠', label: '记忆', labelEn: 'Memory' },
  { path: '/skills', icon: '⚡', label: '技能', labelEn: 'Skills', badge: '8' },
  { path: '/plugins', icon: '🔌', label: '插件', labelEn: 'Plugins' },
  { path: '/workflow', icon: '🔄', label: '工作流', labelEn: 'Workflow' },
  { path: '/models', icon: '🤖', label: '模型', labelEn: 'Models' },
  { path: '/experience', icon: '📚', label: '经验库', labelEn: 'Experience' },
]

const dialogueSubMenu = [
  { path: '/dialogue', icon: '💬', label: '对话列表', labelEn: 'Dialogue List' },
  { path: '/dialogue/history', icon: '📜', label: '历史记录', labelEn: 'History' },
]

const memorySubMenu = [
  { path: '/memory', icon: '🧠', label: '记忆列表', labelEn: 'Memory List' },
  { path: '/memory/categories', icon: '📂', label: '知识分类', labelEn: 'Categories' },
  { path: '/memory/timeline', icon: '📅', label: '时间线', labelEn: 'Timeline' },
]

const skillsSubMenu = [
  { path: '/skills', icon: '⚡', label: '已安装', labelEn: 'Installed' },
  { path: '/market', icon: '🏪', label: '技能市场', labelEn: 'Market' },
]

const pluginsSubMenu = [
  { path: '/plugins', icon: '🔌', label: '已启用插件', labelEn: 'Enabled' },
  { path: '/plugins/mcp', icon: '🔗', label: 'MCP链接', labelEn: 'MCP Links' },
]

const workflowSubMenu = [
  { path: '/workflow', icon: '🔄', label: '流水线列表', labelEn: 'Pipeline List' },
  { path: '/workflow/templates', icon: '📋', label: '模板市场', labelEn: 'Templates' },
]

const modelSubMenu = [
  { path: '/models', icon: '🤖', label: '模型列表', labelEn: 'Model List' },
  { path: '/models/providers', icon: '☁️', label: '提供商配置', labelEn: 'Provider Config' },
  { path: '/models/api', icon: '🔑', label: 'API设置', labelEn: 'API Settings' },
]

const experienceSubMenu = [
  { path: '/experience', icon: '📚', label: '经验列表', labelEn: 'Experience List' },
  { path: '/experience/suggestions', icon: '💡', label: '整合建议', labelEn: 'Suggestions' },
]

const settingsNav = [
  { path: '/system', icon: '🔧', label: '系统设置', labelEn: 'System' },
  { path: '/api', icon: '🔌', label: 'API设置', labelEn: 'API' },
]

const currentSubMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/dialogue')) return dialogueSubMenu
  if (path.startsWith('/memory')) return memorySubMenu
  if (path.startsWith('/skills')) return skillsSubMenu
  if (path.startsWith('/plugins')) return pluginsSubMenu
  if (path.startsWith('/workflow')) return workflowSubMenu
  if (path.startsWith('/models')) return modelSubMenu
  if (path.startsWith('/experience')) return experienceSubMenu
  return []
})
</script>

<style scoped>
.sidebar {
  width: 280px;
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.98) 0%, rgba(15, 23, 42, 0.98) 100%);
  backdrop-filter: blur(20px);
  border-right: 1px solid var(--border);
  padding: 1.75rem;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
}

.sidebar-logo {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  font-weight: bold;
}

.sidebar-title {
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-subtitle {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.nav-menu {
  list-style: none;
  margin-bottom: 1.5rem;
}

.nav-section-title {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: var(--text-secondary);
  padding: 0.5rem 1rem;
  letter-spacing: 0.05em;
}

.nav-item {
  margin-bottom: 0.15rem;
}

.nav-item a {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.3s;
  position: relative;
}

.nav-item a:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  transform: translateX(4px);
}

.nav-item a.active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(139, 92, 246, 0.15));
  color: var(--text-primary);
}

.nav-item a.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: linear-gradient(180deg, var(--primary), var(--secondary));
  border-radius: 0 2px 2px 0;
}

.nav-icon {
  font-size: 1.1rem;
}

.nav-badge {
  margin-left: auto;
  padding: 0.2rem 0.5rem;
  border-radius: 20px;
  font-size: 0.7rem;
  background: var(--primary);
  color: white;
}

.sub-menu {
  border-left: 2px solid var(--border);
  margin-left: 0.5rem;
  padding-left: 0.5rem;
}

.settings-menu {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
}
</style>
