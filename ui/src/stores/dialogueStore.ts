import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'

export interface Dialogue {
  id: string
  title: string
  messages: Message[]
  createdAt: string
  updatedAt: string
  tags: string[]
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'skill'
  content: string
  timestamp: string
  skillName?: string
}

export const useDialogueStore = defineStore('dialogue', () => {
  const dialogues = ref<Dialogue[]>([])
  const currentDialogue = ref<Dialogue | null>(null)
  const loading = ref(false)

  const mockDialogues: Dialogue[] = [
    {
      id: 'd1',
      title: '项目需求分析',
      messages: [
        { id: 'm1', role: 'user', content: '分析这个项目需求', timestamp: new Date().toISOString() },
        { id: 'm2', role: 'assistant', content: '我来帮你分析这个项目需求。首先需要了解项目的背景和目标...', timestamp: new Date().toISOString() },
        { id: 'm3', role: 'skill', content: '调用技能: 代码分析', timestamp: new Date().toISOString(), skillName: '代码执行' },
      ],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      tags: ['需求分析', '项目管理'],
    },
    {
      id: 'd2',
      title: 'API接口设计',
      messages: [
        { id: 'm4', role: 'user', content: '帮我设计RESTful API', timestamp: new Date().toISOString() },
        { id: 'm5', role: 'assistant', content: '好的，我来为你设计RESTful API。根据最佳实践，我建议如下结构...', timestamp: new Date().toISOString() },
      ],
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      updatedAt: new Date().toISOString(),
      tags: ['API设计', '后端'],
    },
    {
      id: 'd3',
      title: '前端组件开发',
      messages: [
        { id: 'm6', role: 'user', content: '创建一个用户登录组件', timestamp: new Date().toISOString() },
        { id: 'm7', role: 'assistant', content: '我来创建一个美观的登录组件，包含表单验证和动画效果。', timestamp: new Date().toISOString() },
        { id: 'm8', role: 'skill', content: '调用技能: UI生成', timestamp: new Date().toISOString(), skillName: '前端生成' },
      ],
      createdAt: new Date(Date.now() - 172800000).toISOString(),
      updatedAt: new Date(Date.now() - 3600000).toISOString(),
      tags: ['前端', 'UI'],
    },
  ]

  async function fetchDialogues() {
    loading.value = true
    try {
      // 开发环境直接使用 mock 数据（注释掉下面一行以启用真实 API）
      throw new Error('Using mock data for development')
      const data = await client.get('/dialogues')
      dialogues.value = data.dialogues || []
    } catch (error) {
      console.log('📦 Using mock data:', error.message)
      dialogues.value = mockDialogues
    } finally {
      loading.value = false
    }
  }

  function createDialogue(title: string = '新对话') {
    const newDialogue: Dialogue = {
      id: `d${Date.now()}`,
      title,
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      tags: [],
    }
    dialogues.value.unshift(newDialogue)
    currentDialogue.value = newDialogue
    return newDialogue
  }

  function addMessage(role: 'user' | 'assistant' | 'skill', content: string, skillName?: string) {
    if (!currentDialogue.value) return
    const message: Message = {
      id: `m${Date.now()}`,
      role,
      content,
      timestamp: new Date().toISOString(),
      skillName,
    }
    currentDialogue.value.messages.push(message)
    currentDialogue.value.updatedAt = new Date().toISOString()
  }

  function selectDialogue(id: string) {
    currentDialogue.value = dialogues.value.find(d => d.id === id) || null
  }

  function deleteDialogue(id: string) {
    dialogues.value = dialogues.value.filter(d => d.id !== id)
    if (currentDialogue.value?.id === id) {
      currentDialogue.value = null
    }
  }

  return {
    dialogues,
    currentDialogue,
    loading,
    fetchDialogues,
    createDialogue,
    addMessage,
    selectDialogue,
    deleteDialogue,
  }
})
