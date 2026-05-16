import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type ThemeName = 'tianqing' | 'mujianzi' | 'zhuhuang' | 'hupo' | 'qianhongsha' | 'shuise' | 'baimu' | 'mogu' | 'tanhuang'

export interface Theme {
  name: string
  nameZh: string
  nameEn: string
  description: string
  primary: string
  primaryDark: string
  primaryLight: string
  secondary: string
  accent: string
  success: string
  warning: string
  danger: string
  info: string
  bgDark: string
  bgCard: string
  bgHover: string
  textPrimary: string
  textSecondary: string
  textMuted: string
  border: string
}

export const themes: Record<ThemeName, Theme> = {
  // 主题1：天青 · 雅
  tianqing: {
    name: 'tianqing',
    nameZh: '天青 · 雅',
    nameEn: 'Sky Blue',
    description: '雨过天青，汝窑本色',
    primary: '#6A9BD1',
    primaryDark: '#4A7BB7',
    primaryLight: '#9EC5E8',
    secondary: '#8B7BA8',
    accent: '#7FB3D3',
    success: '#789262',
    warning: '#CA6924',
    danger: '#F47983',
    info: '#6A9BD1',
    bgDark: '#0F1419',
    bgCard: '#1A1F2E',
    bgHover: '#252B3B',
    textPrimary: '#F8FAFC',
    textSecondary: '#CBD5E1',
    textMuted: '#64748B',
    border: '#334155',
  },
  // 主题2：木簪 · 韵
  mujianzi: {
    name: 'mujianzi',
    nameZh: '木簪 · 韵',
    nameEn: 'Purple Wood',
    description: '紫罗兰色系，淡雅温润',
    primary: '#8B7BA8',
    primaryDark: '#6B5B88',
    primaryLight: '#A89BB8',
    secondary: '#D4868A',
    accent: '#E6B85C',
    success: '#8BA87B',
    warning: '#CA6924',
    danger: '#F47983',
    info: '#8B7BA8',
    bgDark: '#141018',
    bgCard: '#1E1824',
    bgHover: '#2A2430',
    textPrimary: '#FAF5F9',
    textSecondary: '#D4C8D8',
    textMuted: '#8B7BA8',
    border: '#4A3E58',
  },
  // 主题3：竹黄 · 逸
  zhuhuang: {
    name: 'zhuhuang',
    nameZh: '竹黄 · 逸',
    nameEn: 'Bamboo Green',
    description: '竹皮之色，古韵悠然',
    primary: '#789262',
    primaryDark: '#587242',
    primaryLight: '#98B282',
    secondary: '#7FB3D3',
    accent: '#CA6924',
    success: '#789262',
    warning: '#E6B85C',
    danger: '#C47A5A',
    info: '#7FB3D3',
    bgDark: '#0F140D',
    bgCard: '#1A1F16',
    bgHover: '#252B20',
    textPrimary: '#F4F7F2',
    textSecondary: '#C8D8B8',
    textMuted: '#789262',
    border: '#3D4A35',
  },
  // 主题4：琥珀 · 暖
  hupo: {
    name: 'hupo',
    nameZh: '琥珀 · 暖',
    nameEn: 'Amber',
    description: '琥珀之色，温馨活力',
    primary: '#CA6924',
    primaryDark: '#AA4914',
    primaryLight: '#E8A060',
    secondary: '#E6B85C',
    accent: '#C47A5A',
    success: '#789262',
    warning: '#CA6924',
    danger: '#E86B6B',
    info: '#7FB3D3',
    bgDark: '#181008',
    bgCard: '#221810',
    bgHover: '#2E2018',
    textPrimary: '#FEFDFB',
    textSecondary: '#E8D8B8',
    textMuted: '#A88858',
    border: '#4A3520',
  },
  // 主题5：藕色 · 柔
  qianhongsha: {
    name: 'qianhongsha',
    nameZh: '藕色 · 柔',
    nameEn: 'Lotus Pink',
    description: '少女之色，俏皮可爱',
    primary: '#F47983',
    primaryDark: '#D45963',
    primaryLight: '#F8A0A8',
    secondary: '#D4868A',
    accent: '#E6B85C',
    success: '#789262',
    warning: '#CA6924',
    danger: '#F47983',
    info: '#8B7BA8',
    bgDark: '#180F12',
    bgCard: '#22181C',
    bgHover: '#2E2026',
    textPrimary: '#FEF9FA',
    textSecondary: '#F8D8DC',
    textMuted: '#D47983',
    border: '#4A2E36',
  },
  // 主题6：水色 · 清
  shuise: {
    name: 'shuise',
    nameZh: '水色 · 清',
    nameEn: 'Water Clear',
    description: '水之色彩，清新通透',
    primary: '#7FB3D3',
    primaryDark: '#5F93B3',
    primaryLight: '#A8D0E8',
    secondary: '#6A9BD1',
    accent: '#789262',
    success: '#789262',
    warning: '#CA6924',
    danger: '#E86B6B',
    info: '#7FB3D3',
    bgDark: '#0D1418',
    bgCard: '#161F26',
    bgHover: '#202D36',
    textPrimary: '#F0F7FA',
    textSecondary: '#B8D8E8',
    textMuted: '#6F93B3',
    border: '#2E4454',
  },
  // 主题7：白木 · 素
  baimu: {
    name: 'baimu',
    nameZh: '白木 · 素',
    nameEn: 'White Wood',
    description: '素雅纯净，自然质朴',
    primary: '#E8D5C4',
    primaryDark: '#C8B5A4',
    primaryLight: '#F0E5D8',
    secondary: '#8B7BA8',
    accent: '#6A9BD1',
    success: '#789262',
    warning: '#CA6924',
    danger: '#E86B6B',
    info: '#7FB3D3',
    bgDark: '#1A1510',
    bgCard: '#25201A',
    bgHover: '#302A24',
    textPrimary: '#FAF5F0',
    textSecondary: '#E8D5C4',
    textMuted: '#C8B5A4',
    border: '#4A4038',
  },
  // 主题8：墨骨 · 玄
  mogu: {
    name: 'mogu',
    nameZh: '墨骨 · 玄',
    nameEn: 'Ink Black',
    description: '极简深邃，沉稳大气',
    primary: '#6B7280',
    primaryDark: '#4B5563',
    primaryLight: '#9CA3AF',
    secondary: '#6A9BD1',
    accent: '#E8D5C4',
    success: '#6B8E6B',
    warning: '#CA8A04',
    danger: '#EF4444',
    info: '#6A9BD1',
    bgDark: '#0A0A0A',
    bgCard: '#121212',
    bgHover: '#1A1A1A',
    textPrimary: '#F3F4F6',
    textSecondary: '#9CA3AF',
    textMuted: '#6B7280',
    border: '#374151',
  },
  // 主题9：淡黄 · 明
  tanhuang: {
    name: 'tanhuang',
    nameZh: '淡黄 · 明',
    nameEn: 'Light Yellow',
    description: '明亮温暖，积极向上',
    primary: '#E6B85C',
    primaryDark: '#C6983C',
    primaryLight: '#F0D88C',
    secondary: '#CA6924',
    accent: '#789262',
    success: '#789262',
    warning: '#E6B85C',
    danger: '#C47A5A',
    info: '#6A9BD1',
    bgDark: '#181408',
    bgCard: '#221E10',
    bgHover: '#2E2818',
    textPrimary: '#FEFDF8',
    textSecondary: '#F0D88C',
    textMuted: '#C6A85C',
    border: '#4A4028',
  },
}

export const useThemeStore = defineStore('theme', () => {
  const currentTheme = ref<ThemeName>('tianqing')
  const language = ref<'zh' | 'en'>('zh')

  const theme = computed(() => themes[currentTheme.value])

  function setTheme(name: ThemeName) {
    console.log(`[Theme] 🔵 setTheme called: ${name}`)
    console.log(`[Theme] Previous theme: ${currentTheme.value}`)
    
    currentTheme.value = name
    console.log(`[Theme] currentTheme.value updated to: ${name}`)
    
    applyTheme(name)
    console.log(`[Theme] ✅ applyTheme completed for: ${name}`)
    
    localStorage.setItem('qingyue-yinxiang_theme', name)
    console.log(`[Theme] 💾 Saved to localStorage: qingyue-yinxiang_theme = ${name}`)
  }

  function setLanguage(lang: 'zh' | 'en') {
    console.log(`[Theme] 🌍 setLanguage called: ${lang}`)
    language.value = lang
    localStorage.setItem('qingyue-yinxiang_language', lang)
  }

  function applyTheme(name: ThemeName) {
    console.log(`[Theme] 🎨 applyTheme start: ${name}`)
    const t = themes[name]
    
    if (!t) {
      console.error(`[Theme] ❌ Theme not found: ${name}`)
      return
    }
    
    const root = document.documentElement
    
    root.style.setProperty('--primary', t.primary)
    root.style.setProperty('--primary-dark', t.primaryDark)
    root.style.setProperty('--primary-light', t.primaryLight)
    root.style.setProperty('--secondary', t.secondary)
    root.style.setProperty('--accent', t.accent)
    root.style.setProperty('--success', t.success)
    root.style.setProperty('--warning', t.warning)
    root.style.setProperty('--danger', t.danger)
    root.style.setProperty('--info', t.info)
    root.style.setProperty('--bg-dark', t.bgDark)
    root.style.setProperty('--bg-card', t.bgCard)
    root.style.setProperty('--bg-hover', t.bgHover)
    root.style.setProperty('--text-primary', t.textPrimary)
    root.style.setProperty('--text-secondary', t.textSecondary)
    root.style.setProperty('--text-muted', t.textMuted)
    root.style.setProperty('--border', t.border)
    
    console.log(`[Theme] 🎨 CSS variables applied: --primary=${t.primary}, --bg-dark=${t.bgDark}`)
    console.log(`[Theme] ✅ applyTheme end`)
  }

  function init() {
    console.log(`[Theme] 🚀 init() called`)
    const savedTheme = localStorage.getItem('qingyue-yinxiang_theme') as ThemeName | null
    const savedLang = localStorage.getItem('qingyue-yinxiang_language') as 'zh' | 'en' | null
    
    console.log(`[Theme] 📦 localStorage qingyue-yinxiang_theme = ${savedTheme}`)
    console.log(`[Theme] 📦 localStorage qingyue-yinxiang_language = ${savedLang}`)
    
    if (savedTheme && themes[savedTheme]) {
      console.log(`[Theme] 📂 Loading saved theme: ${savedTheme}`)
      setTheme(savedTheme)
    } else {
      console.log(`[Theme] ⭐ Applying default theme: tianqing`)
      applyTheme('tianqing')
    }
    
    if (savedLang) {
      language.value = savedLang
    }
    
    console.log(`[Theme] 🚀 init() completed, currentTheme: ${currentTheme.value}`)
  }

  return { currentTheme, theme, language, setTheme, setLanguage, init }
})
