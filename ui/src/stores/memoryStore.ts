import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'

export interface MemoryEntry {
  id: string
  title: string
  content: string
  category: string
  tags: string[]
  createdAt: string
  updatedAt: string
  source?: string
  professionalDirection?: string
}

export interface KnowledgeItem {
  id: string
  name: string
  description: string
  type: string
  count: number
}

export const useMemoryStore = defineStore('memory', () => {
  const entries = ref<MemoryEntry[]>([])
  const categories = ref<KnowledgeItem[]>([])
  const tags = ref<string[]>([])
  const loading = ref(false)
  const activeDirection = ref<string>('all')

  const professionalDirections = [
    { id: 'writing', name: '写作', nameEn: 'Writing', icon: '✍️' },
    { id: 'coding', name: '编程', nameEn: 'Coding', icon: '💻' },
    { id: 'research', name: '研究', nameEn: 'Research', icon: '🔬' },
    { id: 'design', name: '设计', nameEn: 'Design', icon: '🎨' },
  ]

  const mockEntries: MemoryEntry[] = [
    {
      id: 'mem1',
      title: '项目架构设计原则',
      content: '在设计项目架构时，应该遵循以下原则：模块化、可扩展性、可维护性...',
      category: '架构设计',
      tags: ['架构', '设计模式', '最佳实践'],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      source: '项目需求分析对话',
      professionalDirection: 'coding',
    },
    {
      id: 'mem2',
      title: '文案写作技巧',
      content: '好的文案应该具备以下特点：清晰、简洁、有说服力、能引起共鸣...',
      category: '写作技巧',
      tags: ['文案', '写作', '营销'],
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      updatedAt: new Date().toISOString(),
      source: '内容创作对话',
      professionalDirection: 'writing',
    },
    {
      id: 'mem3',
      title: '市场调研方法论',
      content: '进行市场调研时，可以采用以下方法：问卷调查、深度访谈、竞品分析...',
      category: '市场研究',
      tags: ['调研', '市场', '数据分析'],
      createdAt: new Date(Date.now() - 172800000).toISOString(),
      updatedAt: new Date(Date.now() - 3600000).toISOString(),
      source: '市场分析对话',
      professionalDirection: 'research',
    },
  ]

  const mockCategories: KnowledgeItem[] = [
    { id: 'cat1', name: '架构设计', description: '系统架构相关知识', type: 'coding', count: 12 },
    { id: 'cat2', name: '写作技巧', description: '文案写作方法', type: 'writing', count: 8 },
    { id: 'cat3', name: '市场研究', description: '市场调研方法', type: 'research', count: 6 },
    { id: 'cat4', name: '设计规范', description: 'UI/UX设计规范', type: 'design', count: 10 },
  ]

  async function fetchEntries() {
    loading.value = true
    try {
      const data = await client.get('/memory/entries')
      entries.value = data.entries || []
    } catch {
      entries.value = mockEntries
    } finally {
      loading.value = false
    }
    categories.value = mockCategories
    tags.value = ['架构设计', '写作技巧', '市场研究', '设计规范', '最佳实践', '技术方案']
  }

  function addEntry(entry: Partial<MemoryEntry>) {
    const newEntry: MemoryEntry = {
      id: `mem${Date.now()}`,
      title: entry.title || '新记忆',
      content: entry.content || '',
      category: entry.category || '未分类',
      tags: entry.tags || [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      source: entry.source,
      professionalDirection: entry.professionalDirection,
    }
    entries.value.unshift(newEntry)
    return newEntry
  }

  function deleteEntry(id: string) {
    entries.value = entries.value.filter(e => e.id !== id)
  }

  function searchEntries(keyword: string) {
    if (!keyword.trim()) return entries.value
    return entries.value.filter(e =>
      e.title.includes(keyword) ||
      e.content.includes(keyword) ||
      e.tags.some(t => t.includes(keyword))
    )
  }

  function getEntriesByDirection(direction: string) {
    if (direction === 'all') return entries.value
    return entries.value.filter(e => e.professionalDirection === direction)
  }

  return {
    entries,
    categories,
    tags,
    loading,
    activeDirection,
    professionalDirections,
    fetchEntries,
    addEntry,
    deleteEntry,
    searchEntries,
    getEntriesByDirection,
  }
})
