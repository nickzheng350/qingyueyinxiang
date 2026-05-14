import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type ThemeName = 'tianqing' | 'muban' | 'zhuhuang' | 'hupo' | 'ouse' | 'shuise' | 'jiguang' | 'xinghe' | 'shanshui'

export interface Theme {
  name: string
  nameZh: string
  nameEn: string
  primary: string
  primaryDark: string
  primaryLight: string
  secondary: string
  accent: string
  bgDark: string
  bgLight: string
  bgCard: string
  bgHover: string
  border: string
  textPrimary: string
  textSecondary: string
  success: string
  warning: string
  error: string
  gradient?: string
}

export const themes: Record<ThemeName, Theme> = {
  tianqing: {
    name: 'tianqing',
    nameZh: '天青',
    nameEn: 'Sky Blue',
    primary: '#6A9BD1',
    primaryDark: '#4A7BB7',
    primaryLight: '#9EC5E8',
    secondary: '#5B8DB8',
    accent: '#3D7DC7',
    bgDark: '#1A3A5C',
    bgLight: '#F0F8F8',
    bgCard: 'rgba(26, 58, 92, 0.85)',
    bgHover: 'rgba(106, 155, 209, 0.1)',
    border: 'rgba(106, 155, 209, 0.3)',
    textPrimary: '#E8F4FD',
    textSecondary: '#9EC5E8',
    success: '#4ADE80',
    warning: '#FBBF24',
    error: '#F87171',
  },
  muban: {
    name: 'muban',
    nameZh: '木簪',
    nameEn: 'Wooden Hairpin',
    primary: '#8B6914',
    primaryDark: '#6B5010',
    primaryLight: '#C4A35A',
    secondary: '#A67C00',
    accent: '#D4AF37',
    bgDark: '#3D2E1E',
    bgLight: '#F5F0E6',
    bgCard: 'rgba(61, 46, 30, 0.85)',
    bgHover: 'rgba(139, 105, 20, 0.1)',
    border: 'rgba(139, 105, 20, 0.3)',
    textPrimary: '#F5F0E6',
    textSecondary: '#C4A35A',
    success: '#4ADE80',
    warning: '#FBBF24',
    error: '#F87171',
  },
  zhuhuang: {
    name: 'zhuhuang',
    nameZh: '竹黄',
    nameEn: 'Bamboo Yellow',
    primary: '#C9A227',
    primaryDark: '#A68520',
    primaryLight: '#E8C547',
    secondary: '#D4AF37',
    accent: '#F0D060',
    bgDark: '#3D3518',
    bgLight: '#FAF6E8',
    bgCard: 'rgba(61, 53, 24, 0.85)',
    bgHover: 'rgba(201, 162, 39, 0.1)',
    border: 'rgba(201, 162, 39, 0.3)',
    textPrimary: '#FAF6E8',
    textSecondary: '#E8C547',
    success: '#4ADE80',
    warning: '#FBBF24',
    error: '#F87171',
  },
  hupo: {
    name: 'hupo',
    nameZh: '琥珀',
    nameEn: 'Amber',
    primary: '#D97706',
    primaryDark: '#B45309',
    primaryLight: '#F59E0B',
    secondary: '#F59E0B',
    accent: '#FBBF24',
    bgDark: '#3D2E0E',
    bgLight: '#FEF3C7',
    bgCard: 'rgba(61, 46, 14, 0.85)',
    bgHover: 'rgba(217, 119, 6, 0.1)',
    border: 'rgba(217, 119, 6, 0.3)',
    textPrimary: '#FEF3C7',
    textSecondary: '#F59E0B',
    success: '#4ADE80',
    warning: '#FBBF24',
    error: '#F87171',
  },
  ouse: {
    name: 'ouse',
    nameZh: '藕色',
    nameEn: 'Lotus Root',
    primary: '#C27BA0',
    primaryDark: '#9C5A7C',
    primaryLight: '#E8B4D0',
    secondary: '#D4939D',
    accent: '#E8B4D0',
    bgDark: '#3D2535',
    bgLight: '#FCE8F4',
    bgCard: 'rgba(61, 37, 53, 0.85)',
    bgHover: 'rgba(194, 123, 160, 0.1)',
    border: 'rgba(194, 123, 160, 0.3)',
    textPrimary: '#FCE8F4',
    textSecondary: '#E8B4D0',
    success: '#4ADE80',
    warning: '#FBBF24',
    error: '#F87171',
  },
  shuise: {
    name: 'shuise',
    nameZh: '水色',
    nameEn: 'Aqua',
    primary: '#4ECDC4',
    primaryDark: '#3BA99E',
    primaryLight: '#7EDDD6',
    secondary: '#45B7AA',
    accent: '#5DECE5',
    bgDark: '#1A3D3A',
    bgLight: '#E0F7F5',
    bgCard: 'rgba(26, 61, 58, 0.85)',
    bgHover: 'rgba(78, 205, 196, 0.1)',
    border: 'rgba(78, 205, 196, 0.3)',
    textPrimary: '#E0F7F5',
    textSecondary: '#7EDDD6',
    success: '#4ADE80',
    warning: '#FBBF24',
    error: '#F87171',
  },
  jiguang: {
    name: 'jiguang',
    nameZh: '极光',
    nameEn: 'Aurora',
    primary: '#8B5CF6',
    primaryDark: '#7C3AED',
    primaryLight: '#A78BFA',
    secondary: '#A855F7',
    accent: '#C084FC',
    bgDark: '#2D1B4E',
    bgLight: '#F5F3FF',
    bgCard: 'rgba(45, 27, 78, 0.85)',
    bgHover: 'rgba(139, 92, 246, 0.1)',
    border: 'rgba(139, 92, 246, 0.3)',
    textPrimary: '#F5F3FF',
    textSecondary: '#A78BFA',
    success: '#4ADE80',
    warning: '#FBBF24',
    error: '#F87171',
  },
  xinghe: {
    name: 'xinghe',
    nameZh: '星河',
    nameEn: 'Starry River',
    primary: '#6366F1',
    primaryDark: '#4F46E5',
    primaryLight: '#818CF8',
    secondary: '#7C7CDD',
    accent: '#9BA3F5',
    bgDark: '#1E1B4B',
    bgLight: '#EEF2FF',
    bgCard: 'rgba(30, 27, 75, 0.85)',
    bgHover: 'rgba(99, 102, 241, 0.1)',
    border: 'rgba(99, 102, 241, 0.3)',
    textPrimary: '#EEF2FF',
    textSecondary: '#818CF8',
    success: '#4ADE80',
    warning: '#FBBF24',
    error: '#F87171',
  },
  shanshui: {
    name: 'shanshui',
    nameZh: '山水',
    nameEn: 'Landscape',
    primary: '#10B981',
    primaryDark: '#059669',
    primaryLight: '#34D399',
    secondary: '#2DD4BF',
    accent: '#5EEAD4',
    bgDark: '#1A3D35',
    bgLight: '#ECFDF5',
    bgCard: 'rgba(26, 61, 53, 0.85)',
    bgHover: 'rgba(16, 185, 129, 0.1)',
    border: 'rgba(16, 185, 129, 0.3)',
    textPrimary: '#ECFDF5',
    textSecondary: '#34D399',
    success: '#4ADE80',
    warning: '#FBBF24',
    error: '#F87171',
  },
}

export const useThemeStore = defineStore('theme', () => {
  const currentTheme = ref<ThemeName>('tianqing')
  const language = ref<'zh' | 'en'>('zh')

  const theme = computed(() => themes[currentTheme.value])

  function setTheme(name: ThemeName) {
    currentTheme.value = name
    applyTheme(name)
    localStorage.setItem('hydraflow_theme', name)
  }

  function setLanguage(lang: 'zh' | 'en') {
    language.value = lang
    localStorage.setItem('hydraflow_language', lang)
  }

  function applyTheme(name: ThemeName) {
    const t = themes[name]
    const root = document.documentElement
    root.style.setProperty('--primary', t.primary)
    root.style.setProperty('--primary-dark', t.primaryDark)
    root.style.setProperty('--primary-light', t.primaryLight)
    root.style.setProperty('--secondary', t.secondary)
    root.style.setProperty('--accent', t.accent)
    root.style.setProperty('--bg-dark', t.bgDark)
    root.style.setProperty('--bg-light', t.bgLight)
    root.style.setProperty('--bg-card', t.bgCard)
    root.style.setProperty('--bg-hover', t.bgHover)
    root.style.setProperty('--border', t.border)
    root.style.setProperty('--text-primary', t.textPrimary)
    root.style.setProperty('--text-secondary', t.textSecondary)
    root.style.setProperty('--success', t.success)
    root.style.setProperty('--warning', t.warning)
    root.style.setProperty('--error', t.error)
  }

  function init() {
    const savedTheme = localStorage.getItem('hydraflow_theme') as ThemeName | null
    const savedLang = localStorage.getItem('hydraflow_language') as 'zh' | 'en' | null
    if (savedTheme && themes[savedTheme]) {
      setTheme(savedTheme)
    } else {
      applyTheme('tianqing')
    }
    if (savedLang) {
      language.value = savedLang
    }
  }

  return { currentTheme, theme, language, setTheme, setLanguage, init }
})
