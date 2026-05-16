declare module '@/stores/theme' {
  import { Store } from 'pinia'
  import { Ref } from 'vue'
  
  interface ThemeState {
    language: Ref<string>
  }
  
  interface ThemeStore extends Store<string, ThemeState> {}
  
  export function useThemeStore(): ThemeStore
}
