import { reactive } from 'vue'

// 创建一个响应式的事件总线
const eventBus = reactive({
  currentMonitor: null, // video_url
  monitorList: []
})

export default eventBus
