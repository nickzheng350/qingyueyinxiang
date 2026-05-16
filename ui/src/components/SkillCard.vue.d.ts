declare module '@/components/SkillCard.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{
    skill: any
    showToggle?: boolean
    showInstall?: boolean
  }, {}, {}>
  export default component
}
