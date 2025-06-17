import { reactive } from 'vue'

// 创建一个响应式的事件总线
const eventBus = reactive({
  currentMonitor: null, // video_url
  monitorList: [],

  listeners: {},
  emit(event, ...args) {
    (this.listeners[event] || []).forEach(cb => cb(...args))
  },
  on(event, cb) {
    (this.listeners[event] = this.listeners[event] || []).push(cb)
  },
  off(event, cb) {
    if (!this.listeners[event]) return
    this.listeners[event] = this.listeners[event].filter(fn => fn !== cb)
  }
})

export default eventBus
