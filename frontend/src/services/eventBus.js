import { reactive, computed } from 'vue'
import { encodeMonitorUrl } from '@/services/api.js'

// 创建一个响应式的事件总线
const eventBus = reactive({
  currentMonitor: null, // video_url
  videoFeedUrl: computed(() => {
    if (!eventBus.currentMonitor) return ''
    return `http://localhost:5173/api/monitor/${encodeMonitorUrl(eventBus.currentMonitor)}/video_feed`
  }),
  videoFeedWithFacesUrl: computed(() => {
    if (!eventBus.videoFeedUrl) return ''
    return `${eventBus.videoFeedUrl}_with_faces`
  }),
  monitorList: [],
})

export default eventBus
