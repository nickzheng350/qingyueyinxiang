<template>
  <div class="theme-switch-container">
    <el-dropdown trigger="click" @command="handleThemeChange">
      <div class="theme-toggle-btn">
        <span class="theme-icon">🎨</span>
        <span class="theme-label">{{ currentThemeName }}</span>
        <span class="arrow-icon">▼</span>
      </div>
      
      <template #dropdown>
        <el-dropdown-menu class="theme-dropdown-menu">
          <template v-for="theme in themesList" :key="theme.name">
            <el-dropdown-item :command="theme.name">
              <div class="theme-option">
                <div class="theme-color-preview">
                  <div class="color-dot primary" :style="{ background: theme.primary }"></div>
                  <div class="color-dot secondary" :style="{ background: theme.secondary }"></div>
                  <div class="color-dot accent" :style="{ background: theme.accent }"></div>
                </div>
                <div class="theme-info">
                  <div class="theme-name">{{ theme.nameZh }}</div>
                  <div class="theme-desc">{{ theme.description }}</div>
                </div>
              </div>
            </el-dropdown-item>
          </template>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useThemeStore, themes, type ThemeName } from '@/stores/theme'

const themeStore = useThemeStore()

const themesList = computed(() => Object.values(themes))

const currentThemeName = computed(() => {
  const current = themes[themeStore.currentTheme]
  return current ? current.nameZh : '主题'
})

function handleThemeChange(themeId: string) {
  themeStore.setTheme(themeId as ThemeName)
}
</script>

<style scoped>
.theme-switch-container {
  position: relative;
}

.theme-toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  color: var(--text-primary);
}

.theme-toggle-btn:hover {
  border-color: var(--primary);
  box-shadow: 0 0 12px color-mix(in srgb, var(--primary) 20%, transparent);
}

.theme-icon {
  font-size: 16px;
}

.theme-label {
  font-size: 13px;
  font-weight: 500;
  min-width: 80px;
}

.arrow-icon {
  font-size: 12px;
  color: var(--text-secondary);
}

.theme-dropdown-menu {
  padding: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  min-width: 280px;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  transition: background 0.2s;
}

.theme-option:hover {
  background: var(--bg-hover);
}

.theme-color-preview {
  display: flex;
  gap: 5px;
}

.color-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.theme-info {
  flex: 1;
}

.theme-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.theme-desc {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}
</style>
