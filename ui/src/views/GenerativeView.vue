<template>
  <div>
    <div class="btn-group">
      <button v-for="t in tabs" :key="t.id" class="btn" :class="{ active: activeTab === t.id }" @click="activeTab = t.id">{{ t.icon }} {{ t.label }}</button>
    </div>

    <!-- 文本生成 -->
    <div v-show="activeTab === 'text'" class="card">
      <div class="card-header"><div><div class="card-title">📝 文本生成</div><div class="card-subtitle">使用AI生成高质量文本内容</div></div></div>
      <div class="grid-2">
        <div>
          <el-form label-position="top">
            <el-form-item label="生成类型"><el-select v-model="textForm.type" style="width:100%">
              <el-option v-for="o in textTypes" :key="o.value" :label="o.label" :value="o.value" /></el-select>
            </el-form-item>
            <el-form-item label="输入内容"><el-input v-model="textForm.input" type="textarea" :rows="6" placeholder="输入您的文本或提示..." /></el-form-item>
            <el-form-item label="语气风格"><el-select v-model="textForm.tone" style="width:100%">
              <el-option v-for="o in textTones" :key="o.value" :label="o.label" :value="o.value" /></el-select>
            </el-form-item>
            <button class="btn btn-primary" style="width:100%" @click="generateText" :class="{ 'btn-loading': generating }">✨ 生成文本</button>
          </el-form>
        </div>
        <div>
          <div class="output-box" v-html="textOutput || '<div style=\'text-align:center;padding:3rem;color:var(--text-secondary)\'>📄<p>生成的文本将显示在这里</p></div>'"></div>
          <div style="display:flex;gap:0.5rem;margin-top:0.75rem;">
            <button class="btn btn-secondary btn-sm" @click="copyText" :disabled="!textOutput">📋 复制</button>
            <button class="btn btn-secondary btn-sm" @click="textOutput=''">🗑️ 清空</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 图像生成 -->
    <div v-show="activeTab === 'image'" class="card">
      <div class="card-header"><div><div class="card-title">🖼️ 图像生成</div><div class="card-subtitle">使用AI创作出精美图像</div></div></div>
      <div class="grid-2">
        <div>
          <el-form label-position="top">
            <el-form-item label="艺术风格"><el-select v-model="imageForm.style" style="width:100%">
              <el-option v-for="o in imageStyles" :key="o.value" :label="o.label" :value="o.value" /></el-select>
            </el-form-item>
            <el-form-item label="正向提示词"><el-input v-model="imageForm.prompt" type="textarea" :rows="4" placeholder="描述您想要生成的图像..." /></el-form-item>
            <el-form-item label="分辨率"><el-select v-model="imageForm.res" style="width:100%">
              <el-option label="512×512" value="512x512" /><el-option label="1024×1024" value="1024x1024" /><el-option label="1024×1536" value="1024x1536" /></el-select>
            </el-form-item>
            <button class="btn btn-primary" style="width:100%" @click="generateImage" :class="{ 'btn-loading': generating }">🎨 生成图像</button>
          </el-form>
        </div>
        <div>
          <div class="output-box image-placeholder">🖼️<p>生成的图像将显示在这里</p></div>
        </div>
      </div>
    </div>

    <!-- 音频 -->
    <div v-show="activeTab === 'audio'" class="card">
      <div class="card-header"><div><div class="card-title">🎵 音频生成</div><div class="card-subtitle">生成背景音乐和音效</div></div></div>
      <div class="grid-2">
        <div>
          <el-form label-position="top">
            <el-form-item label="音乐风格"><el-select v-model="audioForm.style" style="width:100%">
              <el-option v-for="o in audioStyles" :key="o.value" :label="o.label" :value="o.value" /></el-select>
            </el-form-item>
            <el-form-item label="描述"><el-input v-model="audioForm.prompt" type="textarea" :rows="3" /></el-form-item>
            <el-form-item label="时长"><el-select v-model="audioForm.duration" style="width:100%">
              <el-option label="30秒" value="30" /><el-option label="1分钟" value="60" /><el-option label="2分钟" value="120" /></el-select>
            </el-form-item>
            <button class="btn btn-primary" style="width:100%" @click="generateAudio" :class="{ 'btn-loading': generating }">🎶 生成音频</button>
          </el-form>
        </div>
        <div class="output-box" style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
          <div style="text-align:center;">🎵<p>生成的音频将在这里播放</p></div>
        </div>
      </div>
    </div>

    <!-- 视频 -->
    <div v-show="activeTab === 'video'" class="card">
      <div class="card-header"><div><div class="card-title">🎬 视频生成</div><div class="card-subtitle">创建AI生成的视频内容</div></div></div>
      <div class="grid-2">
        <div>
          <el-form label-position="top">
            <el-form-item label="视频主题"><el-input v-model="videoForm.theme" placeholder="输入视频主题..." /></el-form-item>
            <el-form-item label="视频描述"><el-input v-model="videoForm.desc" type="textarea" :rows="3" /></el-form-item>
            <el-form-item label="分辨率"><el-select v-model="videoForm.res" style="width:100%">
              <el-option label="720p" value="720p" /><el-option label="1080p" value="1080p" /><el-option label="4K" value="4k" /></el-select>
            </el-form-item>
            <button class="btn btn-primary" style="width:100%" @click="generateVideo" :class="{ 'btn-loading': generating }">🎥 生成视频</button>
          </el-form>
        </div>
        <div class="output-box" style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
          <div style="text-align:center;">🎬<p>生成的视频将在这里播放</p></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const activeTab = ref('text')
const generating = ref(false)
const textOutput = ref('')

const tabs = [
  { id: 'text', label: '文本生成', icon: '📝' },
  { id: 'image', label: '图像生成', icon: '🖼️' },
  { id: 'audio', label: '音频生成', icon: '🎵' },
  { id: 'video', label: '视频生成', icon: '🎬' },
]

const textTypes = [
  { value: 'article', label: '文章创作' },
  { value: 'summary', label: '文本摘要' },
  { value: 'translate', label: '翻译' },
  { value: 'rewrite', label: '改写润色' },
  { value: 'creative', label: '创意写作' },
  { value: 'email', label: '邮件撰写' },
  { value: 'code', label: '代码生成' },
]
const textTones = [
  { value: 'professional', label: '专业正式' },
  { value: 'casual', label: '轻松随意' },
  { value: 'creative', label: '创意文艺' },
  { value: 'technical', label: '技术严谨' },
]
const textForm = ref({ type: 'article', input: '', tone: 'professional' })
const imageForm = ref({ style: 'realistic', prompt: '', res: '1024x1024' })
const imageStyles = [
  { value: 'realistic', label: '写实风格' },
  { value: 'anime', label: '动漫风格' },
  { value: 'cyberpunk', label: '赛博朋克' },
  { value: '3d', label: '3D渲染' },
]
const audioForm = ref({ style: 'ambient', prompt: '', duration: '60' })
const audioStyles = [
  { value: 'ambient', label: '氛围音乐' },
  { value: 'cinematic', label: '电影配乐' },
  { value: 'lofi', label: 'Lo-fi嘻哈' },
]
const videoForm = ref({ theme: '', desc: '', res: '1080p' })

async function generateText() {
  if (!textForm.value.input.trim()) { alert('请输入内容'); return }
  generating.value = true
  await new Promise(r => setTimeout(r, 1500))
  textOutput.value = `<p>这是一段由AI生成的${textForm.value.type === 'article' ? '文章内容' : '创意文本'}。AI技术正在改变我们的生活方式，让创作变得更加高效和便捷。</p>`
  generating.value = false
}
function copyText() { navigator.clipboard.writeText(textOutput.value.replace(/<[^>]+>/g, '')) }
async function generateImage() { generating.value = true; await new Promise(r => setTimeout(r, 2000)); generating.value = false }
async function generateAudio() { generating.value = true; await new Promise(r => setTimeout(r, 2000)); generating.value = false }
async function generateVideo() { generating.value = true; await new Promise(r => setTimeout(r, 2000)); generating.value = false }
</script>

<style scoped>
.gen-tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.card { background: linear-gradient(145deg, var(--bg-card), var(--bg-dark)); border-radius: 16px; border: 1px solid var(--border); padding: 1.75rem; margin-bottom: 1.5rem; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.card-title { font-size: 1.1rem; font-weight: 600; }
.card-subtitle { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.output-box { background: var(--bg-dark); border-radius: 8px; min-height: 300px; padding: 1rem; color: var(--text-secondary); }
.image-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; font-size: 3rem; }
</style>