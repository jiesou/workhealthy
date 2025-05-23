<template>
  <div>
    <h1 class="mb-4">实时监控</h1>
    
    <div class="row mb-4">
      <div class="col-md-8">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span>视频监控</span>
            <span v-if="lastUpdated" class="text-muted small">
              最后更新: {{ lastUpdated }}
            </span>
          </div>
          <div class="card-body text-center">
            <img :src="videoUrl" alt="视频监控" class="img-fluid rounded" style="max-height: 400px;">
          </div>
        </div>
      </div>
      
      <div class="col-md-4">
        <HealthAdvice :metrics="health_metrics" />
      </div>
    </div>
    
    <div class="row mb-4">
      <div class="col-md-3">
        <StatusCard 
          title="人体检测" 
          :status="personDetected ? '已检测到' : '未检测到'" 
          :description="personDetected ? '工位有人' : '工位无人'"
          icon="person"
          :type="personDetected ? 'success' : 'info'"
        />
      </div>
      
      <div class="col-md-3">
        <StatusCard 
          title="活动状态" 
          :status="isActive ? '活动中' : '静止中'" 
          :description="isActive ? '检测到活动' : '未检测到活动'"
          icon="activity"
          :type="isActive ? 'success' : (inactiveTime > 15 ? 'warning' : 'info')"
        />
      </div>
      
      <div class="col-md-3">
        <StatusCard 
          title="水杯检测" 
          :status="cupDetected ? '已检测到' : '未检测到'" 
          :description="cupDetected ? '注意补水' : '记得喝水'"
          icon="cup"
          :type="cupDetected ? 'success' : (sinceCupTime > 60 ? 'warning' : 'info')"
        />
      </div>
      
      <div class="col-md-3">
        <StatusCard 
          title="工作时长" 
          :status="formatSessionWorkDuration" 
          :description="'工作时长'"
          icon="time"
          :type="'success'"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { getStatus, connectWebSocket } from '@/services/api'
import HealthAdvice from '@/components/HealthAdvice.vue'
import StatusCard from '@/components/StatusCard.vue'

export default {
  name: 'Dashboard',
  components: {
    HealthAdvice,
    StatusCard
  },
  data() {
    return {
      videoUrl: ' http://localhost:8081/mjpeg',
      personDetected: false,
      isActive: false,
      cupDetected: false,
      current_session_id: null,
      lastCupTime: null,
      lastActivityTime: null,
      health_metrics: null,
      lastUpdated: null,
      websocket: null,
      // 本地会话计时相关
      sessionWorkDuration: 0, // 累计"有人"时长（秒）
      personStartTime: null,  // 最近一次"开始有人"的时间戳（ms）
      sessionWorkDurationDisplay: 0, // 用于页面显示
      timer: null
    }
  },
  computed: {
    workingDuration() {
      if (!this.workStartTime) return 0
      return Math.floor((new Date() - new Date(this.workStartTime)) / (1000 * 60))
    },
    formatWorkDuration() {
      if (!this.workStartTime) return '未开始'
      
      const minutes = this.workingDuration
      if (minutes < 60) {
        return `${minutes}分钟`
      } else {
        const hours = Math.floor(minutes / 60)
        const remainMinutes = minutes % 60
        return `${hours}小时${remainMinutes}分钟`
      }
    },
    inactiveTime() {
      if (!this.lastActivityTime || this.isActive) return 0
      return Math.floor((new Date() - new Date(this.lastActivityTime)) / (1000 * 60))
    },
    sinceCupTime() {
      if (!this.lastCupTime) return 999
      return Math.floor((new Date() - new Date(this.lastCupTime)) / (1000 * 60))
    },
    workTimeDescription() {
      if (!this.workStartTime) return '未检测到工作'
      
      if (this.workingDuration < 30) {
        return '工作时间较短'
      } else if (this.workingDuration < 120) {
        return '工作时间适中'
      } else {
        return '已工作较长时间'
      }
    },
    workTimeType() {
      if (!this.workStartTime) return 'info'
      
      if (this.workingDuration < 120) {
        return 'success'
      } else if (this.workingDuration < 180) {
        return 'warning'
      } else {
        return 'danger'
      }
    },
    formatSessionWorkDuration() {
      const sec = this.sessionWorkDurationDisplay
      if (!sec || sec <= 0) return '未开始'
      const h = Math.floor(sec / 3600)
      const m = Math.floor((sec % 3600) / 60)
      const s = sec % 60
      if (h > 0) return `${h}小时${m}分${s}秒`
      if (m > 0) return `${m}分${s}秒`
      return `${s}秒`
    }
  },
  methods: {
    // 加载视频流配置
    loadVideoSettings() {
      const savedSettings = localStorage.getItem('workHealthySettings');
      if (savedSettings) {
        try {
          const settings = JSON.parse(savedSettings);
          if (settings.videoProxyUrl) {
            this.videoUrl = settings.videoProxyUrl;
          }
        } catch (e) {
          console.error('解析保存的设置失败:', e);
        }
      }
    },
    // 获取状态
    async fetchStatus() {
      try {
        const response = await getStatus()
        this.updateStatus(response.data)
        this.lastUpdated = new Date().toLocaleTimeString()
      } catch (error) {
        console.error('获取状态出错:', error)
      }
    },
    
    // 更新状态
    updateStatus(status) {
      // 只处理person_detected相关逻辑
      const prevPersonDetected = this.personDetected
      this.personDetected = status.person_detected
      // 进入"有人"状态
      if (this.personDetected && !prevPersonDetected) {
        this.personStartTime = Date.now()
      }
      // 进入"无人"状态
      if (!this.personDetected && prevPersonDetected) {
        if (this.personStartTime) {
          this.sessionWorkDuration += Math.floor((Date.now() - this.personStartTime) / 1000)
          this.personStartTime = null
        }
      }
      // 其余状态同步
      this.isActive = status.is_active
      this.cupDetected = status.cup_detected
      this.current_session_id = status.current_session_id
      if (status.is_active) {
        this.lastActivityTime = new Date()
      }
      if (status.cup_detected) {
        this.lastCupTime = new Date()
      }
      if (status.health_metrics) {
        this.health_metrics = status.health_metrics
      }
    },
    
    // 处理WebSocket消息
    handleWebSocketMessage(data) {
      this.updateStatus(data)
      this.lastUpdated = new Date().toLocaleTimeString()
    },
    
    // 处理WebSocket关闭
    handleWebSocketClose(event) {
      console.log('WebSocket连接已关闭，将尝试重连')
    }
  },
  mounted() {
    // 加载视频流地址
    this.loadVideoSettings();
    
    // 初始获取状态
    this.fetchStatus();
    
    // 连接WebSocket
    this.websocket = connectWebSocket(
      this.handleWebSocketMessage,
      this.handleWebSocketClose
    )
    
    // 启动本地计时器
    this.timer = setInterval(() => {
      if (this.personDetected && this.personStartTime) {
        this.sessionWorkDurationDisplay = this.sessionWorkDuration + Math.floor((Date.now() - this.personStartTime) / 1000)
      } else {
        this.sessionWorkDurationDisplay = this.sessionWorkDuration
      }
    }, 1000)
  },
  beforeUnmount() {
    // 关闭WebSocket连接
    if (this.websocket) {
      this.websocket.close()
    }
    if (this.timer) {
      clearInterval(this.timer)
    }
  }
}
</script> 