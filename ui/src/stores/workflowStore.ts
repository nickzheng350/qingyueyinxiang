import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface SystemStats {
  cpu: number
  memory: number
  gpu: number
  storage: number
}

export const useWorkflowStore = defineStore('workflow', () => {
  const workflows = ref([
    { id: 'content', name: '内容创作流水线', status: 'success', desc: '自动生成文章、优化、发布一站式流程' },
    { id: 'image', name: '图像生成流水线', status: 'success', desc: '提示词生成 → 图像生成 → 后期处理' },
    { id: 'data', name: '数据处理流水线', status: 'pending', desc: '数据采集 → 清洗 → 分析 → 报告' },
    { id: 'audio', name: '音频生成流水线', status: 'success', desc: '文本转语音 → 音效合成 → 混音输出' },
    { id: 'video', name: '视频生成流水线', status: 'warning', desc: '脚本生成 → 图像渲染 → 视频合成' },
    { id: 'custom', name: '自定义流水线', status: 'success', desc: '自由组合节点创建自定义流程' },
  ])

  const nodes = ref<any[]>([])
  const edges = ref<any[]>([])

  return { workflows, nodes, edges }
})