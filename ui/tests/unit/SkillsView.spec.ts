import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import SkillsView from '@/views/SkillsView.vue'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'

vi.mock('@/api/client', () => ({
  client: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

vi.mock('@/stores/skillStore', () => ({
  useSkillStore: vi.fn(() => ({
    installed: ref([]),
    market: ref([]),
    loading: ref(false),
    fetchInstalled: vi.fn().mockResolvedValue(undefined),
    fetchMarket: vi.fn().mockResolvedValue(undefined),
    installSkill: vi.fn(),
    uninstallSkill: vi.fn(),
    toggleSkill: vi.fn()
  }))
}))

vi.mock('@/stores/theme', () => ({
  useThemeStore: vi.fn(() => ({
    language: ref('zh-CN')
  }))
}))

describe('SkillsView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should toggle skill enabled state', () => {
    const skill = { id: '1', name: 'Test', enabled: true }
    
    const wrapper = shallowMount(SkillsView)
    wrapper.vm.toggleSkill(skill)
    expect(skill.enabled).toBe(false)
    
    wrapper.vm.toggleSkill(skill)
    expect(skill.enabled).toBe(true)
  })

  it('should filter by direction', () => {
    const wrapper = shallowMount(SkillsView)
    wrapper.vm.activeDirection = 'tool'
    wrapper.vm.market = [
      { id: '1', name: 'Web Search', type: 'tool' },
      { id: '2', name: 'Skill A', type: 'skill' },
      { id: '3', name: 'File Manager', type: 'tool' }
    ]
    
    const filtered = wrapper.vm.filteredMarket
    expect(filtered.length).toBe(2)
    expect(filtered.every(s => s.type === 'tool')).toBe(true)
  })

  it('should show all skills when direction is all', () => {
    const wrapper = shallowMount(SkillsView)
    wrapper.vm.activeDirection = 'all'
    wrapper.vm.market = [
      { id: '1', name: 'Web Search', type: 'tool' },
      { id: '2', name: 'Skill A', type: 'skill' }
    ]
    
    const filtered = wrapper.vm.filteredMarket
    expect(filtered.length).toBe(2)
  })

  it('should calculate enabled and disabled counts', () => {
    const wrapper = shallowMount(SkillsView)
    wrapper.vm.installed = [
      { id: '1', enabled: true },
      { id: '2', enabled: true },
      { id: '3', enabled: false }
    ]
    
    expect(wrapper.vm.enabledCount).toBe(2)
    expect(wrapper.vm.disabledCount).toBe(1)
  })
})