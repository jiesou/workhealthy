import { reactive } from 'vue'

// 创建一个响应式的事件总线
const eventBus = reactive({
  currentCamera: null,
  listeners: {},
  
  // 发射事件
  emit(event, ...args) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(...args))
    }
  },
  
  // 监听事件
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
    this.listeners[event].push(callback)
  },
  
  // 移除事件监听
  off(event, callback) {
    if (this.listeners[event]) {
      const index = this.listeners[event].indexOf(callback)
      if (index > -1) {
        this.listeners[event].splice(index, 1)
      }
    }
  },
  
  // 设置当前摄像头
  setCurrentCamera(camera) {
    this.currentCamera = camera
    this.emit('camera-changed', camera)
  }
})

export default eventBus
