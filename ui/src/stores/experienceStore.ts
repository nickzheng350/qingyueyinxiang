import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'

export interface Experience {
  id: string
  name: string
  description: string
  sourceDialogue?: string
  professionalDirection: string
  tags: string[]
  createdAt: string
  usageCount: number
  quality: number
}

export const useExperienceStore = defineStore('experience', () => {
  const experiences = ref<Experience[]>([])
  const loading = ref(false)
  const activeDirection = ref<string>('all')

  const professionalDirections = [
    { id: 'writing', name: '写作', nameEn: 'Writing', icon: '✍️' },
    { id: 'coding', name: '编程', nameEn: 'Coding', icon: '💻' },
    { id: 'research', name: '研究', nameEn: 'Research', icon: '🔬' },
    { id: 'design', name: '设计', nameEn: 'Design', icon: '🎨' },
  ]

  const mockExperiences: Experience[] = [
    {
      id: 'exp1',
      name: 'Vue3组件开发模式',
      description: '总结了一套高效的Vue3组件开发流程，包括组合式API使用、状态管理模式、组件通信技巧等。',
      sourceDialogue: '前端组件开发对话',
      professionalDirection: 'coding',
      tags: ['Vue3', '组件', '最佳实践'],
      createdAt: new Date().toISOString(),
      usageCount: 24,
      quality: 92,
    },
    {
      id: 'exp2',
      name: '技术文档写作框架',
      description: '一套完整的技术文档写作框架，包含概述、背景、方案设计、代码示例、总结等模块。',
      sourceDialogue: 'API文档编写对话',
      professionalDirection: 'writing',
      tags: ['文档', '技术写作', '模板'],
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      usageCount: 18,
      quality: 88,
    },
    {
      id: 'exp3',
      name: '市场竞品分析方法',
      description: '通过多维度分析竞品，包括功能对比、用户体验、定价策略、市场定位等。',
      sourceDialogue: '竞品分析对话',
      professionalDirection: 'research',
      tags: ['竞品分析', '市场研究', '方法论'],
      createdAt: new Date(Date.now() - 172800000).toISOString(),
      usageCount: 12,
      quality: 85,
    },
    {
      id: 'exp4',
      name: 'UI设计系统构建',
      description: '从0到1构建设计系统，包括色彩体系、字体系统、组件库设计规范。',
      sourceDialogue: '设计系统搭建对话',
      professionalDirection: 'design',
      tags: ['设计系统', 'UI规范', '组件库'],
      createdAt: new Date(Date.now() - 259200000).toISOString(),
      usageCount: 15,
      quality: 90,
    },
  ]

  async function fetchExperiences() {
    loading.value = true
    try {
      const data = await client.get('/experiences')
      experiences.value = data.experiences || []
    } catch {
      experiences.value = mockExperiences
    } finally {
      loading.value = false
    }
  }

  function addExperience(exp: Partial<Experience>) {
    const newExp: Experience = {
      id: `exp${Date.now()}`,
      name: exp.name || '新经验',
      description: exp.description || '',
      sourceDialogue: exp.sourceDialogue,
      professionalDirection: exp.professionalDirection || 'coding',
      tags: exp.tags || [],
      createdAt: new Date().toISOString(),
      usageCount: 0,
      quality: exp.quality || 80,
    }
    experiences.value.unshift(newExp)
    return newExp
  }

  function deleteExperience(id: string) {
    experiences.value = experiences.value.filter(e => e.id !== id)
  }

  function getExperiencesByDirection(direction: string) {
    if (direction === 'all') return experiences.value
    return experiences.value.filter(e => e.professionalDirection === direction)
  }

  async function generateFromDialogue(dialogueId: string) {
    loading.value = true
    try {
      const data = await client.post(`/experiences/generate/${dialogueId}`)
      if (data.experience) {
        experiences.value.unshift(data.experience)
      }
      return data
    } catch {
      return { status: 'mock', message: '模拟生成经验' }
    } finally {
      loading.value = false
    }
  }

  async function getSuggestions() {
    try {
      const data = await client.get('/experiences/suggestions')
      return data.suggestions || []
    } catch {
      return [
        { type: 'merge', message: '建议合并: "Vue组件开发"和"React组件开发"', ids: ['exp1'] },
        { type: 'optimize', message: '建议优化: "技术文档写作框架"可以增加更多示例', id: 'exp2' },
      ]
    }
  }

  return {
    experiences,
    loading,
    activeDirection,
    professionalDirections,
    fetchExperiences,
    addExperience,
    deleteExperience,
    getExperiencesByDirection,
    generateFromDialogue,
    getSuggestions,
  }
})
