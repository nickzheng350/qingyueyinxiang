import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import FilesView from '@/views/FilesView.vue'

describe('FilesView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should be importable', () => {
    expect(FilesView).toBeDefined()
  })
})