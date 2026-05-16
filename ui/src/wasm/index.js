// WASM 模块自动加载器
import init, * as wasm from './skill_engine.js'

let initialized = false

export async function initWasm() {
  if (initialized) return
  await init()
  initialized = true
}

export * from './skill_engine.js'
export default wasm
