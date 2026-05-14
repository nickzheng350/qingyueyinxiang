import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'

export interface Skill {
  id: string
  name: string
  description: string
  type: string
  enabled: boolean
  installed: boolean
}

export const useSkillStore = defineStore('skill', () => {
  const installed = ref<Skill[]>([])
  const market = ref<Skill[]>([])
  const loading = ref(false)

  async function fetchInstalled() {
    loading.value = true
    try {
      const data = await client.get('/skills')
      installed.value = data.skills || []
    } catch {
      installed.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchMarket() {
    loading.value = true
    try {
      const data = await client.get('/skills/market')
      market.value = data.skills || []
    } catch {
      market.value = []
    } finally {
      loading.value = false
    }
  }

  return { installed, market, loading, fetchInstalled, fetchMarket }
})