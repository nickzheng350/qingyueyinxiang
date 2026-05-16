declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '@/components/SkillCard.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{
    skill: any
    showToggle?: boolean
    showInstall?: boolean
  }, {}, {}>
  export default component
}

declare module '@/stores/skillStore' {
  import { Store } from 'pinia'
  
  interface SkillState {
    installed: any[]
    market: any[]
    loading: boolean
  }
  
  interface SkillStore extends Store<string, SkillState> {
    fetchInstalled(): Promise<void>
    fetchMarket(): Promise<void>
  }
  
  export function useSkillStore(): SkillStore
}

declare module '@/stores/theme' {
  import { Store } from 'pinia'
  import { Ref } from 'vue'
  
  interface ThemeState {
    language: Ref<string>
  }
  
  interface ThemeStore extends Store<string, ThemeState> {}
  
  export function useThemeStore(): ThemeStore
}

declare module '@/api/client' {
  export const client: {
    get(url: string): Promise<any>
    post(url: string, data?: any): Promise<any>
  }
}

declare module '@/stores/modelStore' {
  import { Store } from 'pinia'
  import { Ref } from 'vue'
  
  interface ModelState {
    models: any[]
    loading: boolean
  }
  
  interface ModelStore extends Store<string, ModelState> {
    fetchModels(): Promise<void>
    addModel(model: any): Promise<void>
    deleteModel(id: string): Promise<void>
    toggleModel(id: string): Promise<void>
  }
  
  export function useModelStore(): ModelStore
}
