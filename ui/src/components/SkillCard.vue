<template>
  <div class="skill-card" :class="{ disabled: showToggle && !skill.enabled }">
    <div class="skill-header">
      <div class="skill-icon">
        {{ getSkillIcon(skill.type) }}
      </div>
      <div class="skill-name-col">
        <div class="skill-name">{{ lang === 'zh' ? skill.name : (skill.nameEn || skill.name) }}</div>
        <span class="skill-type">{{ skill.type }}</span>
      </div>
    </div>
    <div class="skill-desc">{{ skill.description }}</div>
    <div class="skill-actions">
      <button v-if="showInstall && !skill.installed" class="btn btn-primary btn-sm" @click="$emit('install', skill)">
        {{ lang === 'zh' ? '安装' : 'Install' }}
      </button>
      <button v-if="showToggle" class="btn btn-secondary btn-sm" @click="$emit('toggle', skill)">
        {{ skill.enabled ? (lang === 'zh' ? '禁用' : 'Disable') : (lang === 'zh' ? '启用' : 'Enable') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'
import { storeToRefs } from 'pinia'

defineProps<{ skill: any; showToggle?: boolean; showInstall?: boolean }>()
defineEmits(['install', 'toggle'])

const themeStore = useThemeStore()
const { language: lang } = storeToRefs(themeStore)

function getSkillIcon(type: string) {
  const icons: Record<string, string> = {
    code: '💻',
    system: '⚙️',
    web: '🌐',
    ai: '🤖',
    media: '🎬',
    data: '📊',
  }
  return icons[type] || '⚡'
}
</script>

<style scoped>
.skill-card {
  background: linear-gradient(145deg, var(--bg-card), rgba(15, 23, 42, 0.8));
  border-radius: 16px;
  padding: 1.75rem;
  border: 1px solid var(--border);
  transition: all 0.4s;
}
.skill-card:hover { border-color: var(--primary); transform: translateY(-4px); box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15); }
.skill-card.disabled { opacity: 0.5; }
.skill-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; gap: 1rem; }
.skill-icon { font-size: 2rem; }
.skill-name-col { flex: 1; }
.skill-name { font-size: 1.1rem; font-weight: 600; }
.skill-type { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.7rem; background: color-mix(in srgb, var(--primary) 20%, transparent); color: white; margin-top: 0.25rem; }
.skill-desc { color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem; line-height: 1.5; }
.skill-actions { display: flex; gap: 0.5rem; }
</style>