import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'

export interface Plugin {
  id: string
  name: string
  nameEn: string
  description: string
  version: string
  author: string
  enabled: boolean
  dependencies: string[]
  category: string
  installedAt?: string
}

export interface MCPLink {
  id: string
  name: string
  url: string
  status: 'connected' | 'disconnected' | 'error'
  lastSync?: string
}

export const usePluginStore = defineStore('plugin', () => {
  const enabledPlugins = ref<Plugin[]>([])
  const disabledPlugins = ref<Plugin[]>([])
  const mcpLinks = ref<MCPLink[]>([])
  const loading = ref(false)
  const activeTab = ref<'enabled' | 'disabled' | 'mcp'>('enabled')

  const mockEnabledPlugins: Plugin[] = [
    { id: 'p1', name: '代码执行', nameEn: 'Code Execution', description: '安全执行Python/JS代码片段', version: '1.2.0', author: '清悦印象团队', enabled: true, dependencies: [], category: 'core', installedAt: new Date().toISOString() },
    { id: 'p2', name: '文件处理', nameEn: 'File Processing', description: '文件的读取、写入、压缩、解压', version: '1.1.5', author: '清悦印象团队', enabled: true, dependencies: ['p1'], category: 'core', installedAt: new Date().toISOString() },
    { id: 'p3', name: '网页搜索', nameEn: 'Web Search', description: '搜索互联网内容', version: '2.0.0', author: '清悦印象团队', enabled: true, dependencies: [], category: 'web', installedAt: new Date(Date.now() - 86400000).toISOString() },
    { id: 'p4', name: '图像处理', nameEn: 'Image Processing', description: '图像识别、生成、编辑', version: '1.5.0', author: '清悦印象团队', enabled: true, dependencies: ['p2'], category: 'ai', installedAt: new Date(Date.now() - 172800000).toISOString() },
  ]

  const mockDisabledPlugins: Plugin[] = [
    { id: 'p5', name: '视频处理', nameEn: 'Video Processing', description: '视频剪辑、转码、特效', version: '1.0.0', author: '清悦印象团队', enabled: false, dependencies: ['p4'], category: 'media', installedAt: new Date(Date.now() - 259200000).toISOString() },
    { id: 'p6', name: '音频处理', nameEn: 'Audio Processing', description: '音频剪辑、转码、分析', version: '1.0.0', author: '清悦印象团队', enabled: false, dependencies: [], category: 'media', installedAt: new Date(Date.now() - 259200000).toISOString() },
    { id: 'p7', name: '数据可视化', nameEn: 'Data Visualization', description: '图表生成、数据看板', version: '0.9.0', author: 'Community', enabled: false, dependencies: ['p1', 'p2'], category: 'analytics', installedAt: new Date(Date.now() - 345600000).toISOString() },
  ]

  const mockMCPLinks: MCPLink[] = [
    { id: 'mcp1', name: 'GitHub集成', url: 'https://api.github.com', status: 'connected', lastSync: new Date().toISOString() },
    { id: 'mcp2', name: 'Notion同步', url: 'https://api.notion.com', status: 'connected', lastSync: new Date(Date.now() - 3600000).toISOString() },
    { id: 'mcp3', name: 'Slack通知', url: 'https://slack.com/api', status: 'disconnected' },
    { id: 'mcp4', name: 'Figma设计稿', url: 'https://api.figma.com', status: 'error' },
  ]

  async function fetchPlugins() {
    loading.value = true
    try {
      const [enabledData, disabledData] = await Promise.all([
        client.get('/plugins/enabled').catch(() => ({ plugins: [] })),
        client.get('/plugins/disabled').catch(() => ({ plugins: [] })),
      ])
      enabledPlugins.value = enabledData.plugins || mockEnabledPlugins
      disabledPlugins.value = disabledData.plugins || mockDisabledPlugins
    } catch {
      enabledPlugins.value = mockEnabledPlugins
      disabledPlugins.value = mockDisabledPlugins
    } finally {
      loading.value = false
    }
    mcpLinks.value = mockMCPLinks
  }

  function togglePlugin(id: string) {
    const enabledIdx = enabledPlugins.value.findIndex(p => p.id === id)
    const disabledIdx = disabledPlugins.value.findIndex(p => p.id === id)

    if (enabledIdx !== -1) {
      const plugin = enabledPlugins.value.splice(enabledIdx, 1)[0]
      plugin.enabled = false
      disabledPlugins.value.push(plugin)
    } else if (disabledIdx !== -1) {
      const plugin = disabledPlugins.value.splice(disabledIdx, 1)[0]
      plugin.enabled = true
      enabledPlugins.value.push(plugin)
    }
  }

  function addMCPLink(link: Partial<MCPLink>) {
    const newLink: MCPLink = {
      id: `mcp${Date.now()}`,
      name: link.name || '新链接',
      url: link.url || '',
      status: 'disconnected',
    }
    mcpLinks.value.push(newLink)
    return newLink
  }

  function removeMCPLink(id: string) {
    mcpLinks.value = mcpLinks.value.filter(l => l.id !== id)
  }

  async function syncMCPLink(id: string) {
    const link = mcpLinks.value.find(l => l.id === id)
    if (link) {
      link.status = 'connected'
      link.lastSync = new Date().toISOString()
    }
  }

  return {
    enabledPlugins,
    disabledPlugins,
    mcpLinks,
    loading,
    activeTab,
    fetchPlugins,
    togglePlugin,
    addMCPLink,
    removeMCPLink,
    syncMCPLink,
  }
})
