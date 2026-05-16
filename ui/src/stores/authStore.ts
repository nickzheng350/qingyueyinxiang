import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ApiSettings {
  apiKey: string
  apiUrl: string
  apiType: string
  apiTypeName: string
  defaultModel: string
}

export const useAuthStore = defineStore('auth', () => {
  const settings = ref<ApiSettings | null>(null)

  function loadSettings() {
    const raw = localStorage.getItem('qingyue-yinxiang_api_settings')
    if (raw) {
      settings.value = JSON.parse(raw)
    }
  }

  function saveSettings(data: ApiSettings) {
    settings.value = data
    localStorage.setItem('qingyue-yinxiang_api_settings', JSON.stringify(data))
  }

  function clearSettings() {
    settings.value = null
    localStorage.removeItem('qingyue-yinxiang_api_settings')
  }

  loadSettings()

  return { settings, loadSettings, saveSettings, clearSettings }
})