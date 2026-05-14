import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'

export interface ModelProvider {
  id: string
  name: string
  nameEn: string
  logo: string
  category: 'official' | 'local'
}

export interface Model {
  id: string
  name: string
  provider: string
  category: string
  functionType: string
  enabled: boolean
  status: 'online' | 'offline' | 'error'
  config: Record<string, string>
}

export const useModelStore = defineStore('model', () => {
  const providers = ref<ModelProvider[]>([
    { id: 'openai', name: 'OpenAI', nameEn: 'OpenAI', logo: '🤖', category: 'official' },
    { id: 'anthropic', name: 'Anthropic', nameEn: 'Anthropic', logo: '🧠', category: 'official' },
    { id: 'minimax', name: 'MiniMax', nameEn: 'MiniMax', logo: '🔷', category: 'official' },
    { id: 'ali', name: '阿里云', nameEn: 'Alibaba Cloud', logo: '🔶', category: 'official' },
    { id: 'google', name: 'Google', nameEn: 'Google', logo: '🔵', category: 'official' },
    { id: 'ollama', name: 'Ollama', nameEn: 'Ollama', logo: '🦙', category: 'local' },
    { id: 'lmstudio', name: 'LM Studio', nameEn: 'LM Studio', logo: '💜', category: 'local' },
    { id: 'custom', name: '自定义', nameEn: 'Custom Endpoint', logo: '⚙️', category: 'local' },
  ])

  const models = ref<Model[]>([])
  const loading = ref(false)
  const activeProvider = ref<string>('')
  const activeFunction = ref<string>('all')

  const functionTypes = [
    { id: 'text', name: '文本生成', nameEn: 'Text Generation', icon: '✏️' },
    { id: 'image', name: '图像生成', nameEn: 'Image Generation', icon: '🖼️' },
    { id: 'audio', name: '音频生成', nameEn: 'Audio Generation', icon: '🎵' },
    { id: 'embedding', name: '向量嵌入', nameEn: 'Embedding', icon: '📊' },
  ]

  const mockModels: Model[] = [
    { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai', category: 'text', functionType: 'text', enabled: true, status: 'online', config: { apiKey: '****', baseUrl: '' } },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai', category: 'text', functionType: 'text', enabled: true, status: 'online', config: { apiKey: '****', baseUrl: '' } },
    { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'anthropic', category: 'text', functionType: 'text', enabled: true, status: 'online', config: { apiKey: '****' } },
    { id: 'minimax-m2', name: 'MiniMax-M2', provider: 'minimax', category: 'text', functionType: 'text', enabled: true, status: 'online', config: { apiKey: '****', groupId: '****' } },
    { id: 'qwen2.5', name: '通义千问2.5', provider: 'ali', category: 'text', functionType: 'text', enabled: false, status: 'offline', config: { apiKey: '****' } },
    { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', provider: 'google', category: 'text', functionType: 'text', enabled: false, status: 'offline', config: { apiKey: '****' } },
    { id: 'llama3.1', name: 'Llama 3.1', provider: 'ollama', category: 'text', functionType: 'text', enabled: true, status: 'online', config: { baseUrl: 'http://localhost:11434' } },
    { id: 'dall-e-3', name: 'DALL-E 3', provider: 'openai', category: 'image', functionType: 'image', enabled: true, status: 'online', config: { apiKey: '****' } },
    { id: 'sdxl', name: 'SDXL', provider: 'custom', category: 'image', functionType: 'image', enabled: false, status: 'offline', config: { baseUrl: 'http://localhost:7860' } },
  ]

  async function fetchModels() {
    loading.value = true
    try {
      const data = await client.get('/models')
      models.value = data.models || []
    } catch {
      models.value = mockModels
    } finally {
      loading.value = false
    }
  }

  function getModelsByProvider(providerId: string) {
    if (!providerId) return models.value
    return models.value.filter(m => m.provider === providerId)
  }

  function getModelsByFunction(functionType: string) {
    if (functionType === 'all') return models.value
    return models.value.filter(m => m.functionType === functionType)
  }

  function toggleModel(id: string) {
    const model = models.value.find(m => m.id === id)
    if (model) {
      model.enabled = !model.enabled
    }
  }

  function updateModelConfig(id: string, config: Record<string, string>) {
    const model = models.value.find(m => m.id === id)
    if (model) {
      model.config = { ...model.config, ...config }
    }
  }

  function addModel(model: Partial<Model>) {
    const newModel: Model = {
      id: model.id || `model_${Date.now()}`,
      name: model.name || '新模型',
      provider: model.provider || 'custom',
      category: model.category || 'text',
      functionType: model.functionType || 'text',
      enabled: model.enabled ?? true,
      status: model.status || 'offline',
      config: model.config || {},
    }
    models.value.push(newModel)
    return newModel
  }

  return {
    providers,
    models,
    loading,
    activeProvider,
    activeFunction,
    functionTypes,
    fetchModels,
    getModelsByProvider,
    getModelsByFunction,
    toggleModel,
    updateModelConfig,
    addModel,
  }
})
