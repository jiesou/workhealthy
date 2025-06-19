<template>
  <div class="dashboard-container">
    <h1 class="dashboard-title">实时监控</h1>

    <div class="dashboard-grid">
      <div class="video-section">
        <div class="glass-card">
          <div class="card-header">
            <span class="header-title">视频监控</span>
            <span v-if="lastUpdated" class="update-time">
              最后更新: {{ lastUpdated }}
            </span>
          </div>
          <div class="video-container">
            <img :src="eventBus.videoFeedUrl" alt="视频监控" class="video-feed">
            <div class="video-overlay" v-if="!eventBus.videoFeedUrl">
              <div class="loading-spinner"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="health-section">
        <HealthAdvice :metrics="healthMetrics" />
      </div>
    </div>

    <div class="status-grid">
      <StatusCard title="人体检测" :status="personDetected ? '已检测到' : '未检测到'"
        :description="personDetected ? '工位有人' : '工位无人'" icon="person" :type="personDetected ? 'success' : 'info'" />

      <StatusCard title="活动状态" :status="isActive ? '活动中' : '静止中'" :description="isActive ? '检测到活动' : '未检测到活动'"
        icon="activity" :type="isActive ? 'success' : (inactiveTime > 15 ? 'warning' : 'info')" />

      <StatusCard title="水杯检测" :status="cupDetected ? '已检测到' : '未检测到'" :description="cupDetected ? '注意补水' : '记得喝水'"
        icon="cup" :type="cupDetected ? 'success' : (sinceCupTime > 60 ? 'warning' : 'info')" />

      <StatusCard title="当前功率" :status="currentPowerMessage || '加载中...'" description="工位插座"
        icon="current" :type="currentPowerMessage ? 'success' : 'info'" />

      <StatusCard title="工作时长" :status="todayWorkDurationMessage" description="工作时长" icon="time" type="success" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, watch } from 'vue'
import { connectWebSocket } from '@/services/api'
import HealthAdvice from '@/components/HealthAdvice.vue';
import StatusCard from '@/components/StatusCard.vue'
import eventBus from '@/services/eventBus'

// 响应式状态
const personDetected = ref(false)
const isActive = ref(false)
const cupDetected = ref(false)
const lastCupTime = ref(null)
const lastActivityTime = ref(null)
const healthMetrics = ref(null);
const currentPowerMessage = ref('');
const lastUpdated = ref(null)
const websocket = ref(null)

// Work duration display
// const backendWorkDuration = ref(0); // Removed
const todayWorkDurationMessage = ref('加载中...'); // Added

const inactiveTime = computed(() => {
  if (!lastActivityTime.value || isActive.value) return 0
  return Math.floor((new Date() - new Date(lastActivityTime.value)) / (1000 * 60))
})

const sinceCupTime = computed(() => {
  if (!lastCupTime.value) return 999
  return Math.floor((new Date() - new Date(lastCupTime.value)) / (1000 * 60))
})

// formatSessionWorkDuration computed property removed

const updateStatus = (status) => {
  // Client-side work duration calculation removed
  personDetected.value = status.person_detected;

  // Update todayWorkDurationMessage from WebSocket status
  todayWorkDurationMessage.value = status.today_work_duration_message || '---';

  // 更新其他状态
  isActive.value = status.is_active
  cupDetected.value = status.cup_detected

  if (status.is_active) {
    lastActivityTime.value = new Date()
  }

  if (status.cup_detected) {
    lastCupTime.value = new Date()
  }

  // health_metrics update removed
  // Restore healthMetrics update (it will likely remain null as health_metrics is not in output_insights)
  if (status.health_metrics) {
    healthMetrics.value = status.health_metrics;
  }

  if (status.current_power_message) {
    currentPowerMessage.value = status.current_power_message;
  }
}

// startTimer method removed

watch(() => eventBus.currentMonitor, (newCamera) => {
  if (newCamera) {
    // 关闭旧的WebSocket连接
    if (websocket.value) {
      websocket.value.close()
    }

    // 重新连接WebSocket
    websocket.value = connectWebSocket(
      (data) => {
        updateStatus(data)
        lastUpdated.value = new Date().toLocaleTimeString()
      },
      eventBus.currentMonitor
    )
  }
}, { immediate: true })

onBeforeUnmount(() => {
  // 关闭WebSocket连接
  if (websocket.value) {
    websocket.value.close()
  }
})
</script>

<style scoped>
.dashboard-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-title {
  font-size: 2.5rem;
  font-weight: 600;
  margin-bottom: 2rem;
  color: #1d1d1f;
  letter-spacing: -0.5px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  /* Changed back from 1fr */
  gap: 2rem;
  margin-bottom: 2rem;
}

.video-section {
  position: relative;
}

.glass-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.3s ease;
}

.glass-card:hover {
  transform: translateY(-5px);
}

.card-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1d1d1f;
}

.update-time {
  font-size: 0.875rem;
  color: #86868b;
}

.video-container {
  position: relative;
  padding: 1rem;
  background: #f5f5f7;
  border-radius: 0 0 20px 20px;
}

.video-feed {
  width: 100%;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #0071e3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1.5rem;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

@media (max-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .status-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 1rem;
  }

  .status-grid {
    grid-template-columns: 1fr;
  }
}
</style>