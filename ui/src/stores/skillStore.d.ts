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
