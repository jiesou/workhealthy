<template>
  <div class="health-advice">
    <div class="advice-header">
      <h3>健康建议</h3>
    </div>
    <div class="advice-content">
      <div v-if="!metrics" class="empty-state">
        <div class="empty-icon">
          <i class="bi bi-heart"></i>
        </div>
        <p>暂无健康数据</p>
      </div>
      <div v-else class="advice-list">
        <div class="advice-item" v-if="!metrics.cup_detected">
          <div class="advice-icon warning">
            <i class="bi bi-cup-straw"></i>
          </div>
          <div class="advice-text">
            <h4>补水建议</h4>
            <p>记得喝水，保持水分充足</p>
          </div>
        </div>
        <div class="advice-item" v-if="!metrics.is_active">
          <div class="advice-icon warning">
            <i class="bi bi-activity"></i>
          </div>
          <div class="advice-text">
            <h4>活动建议</h4>
            <p>建议起身活动，避免久坐</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HealthAdvice',
  props: {
    metrics: {
      type: Object,
      default: null
    }
  }
}
</script>

<style scoped>
.health-advice {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.advice-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.advice-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1d1d1f;
}

.advice-content {
  padding: 1.5rem;
  flex: 1;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #86868b;
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: #86868b;
}

.advice-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.advice-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 12px;
  transition: transform 0.3s ease;
}

.advice-item:hover {
  transform: translateX(5px);
}

.advice-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.advice-icon.warning {
  background: rgba(255, 204, 0, 0.1);
  color: #ffcc00;
}

.advice-text {
  flex: 1;
}

.advice-text h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1d1d1f;
}

.advice-text p {
  margin: 0;
  font-size: 0.875rem;
  color: #86868b;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .advice-header {
    padding: 1.25rem;
  }
  
  .advice-content {
    padding: 1.25rem;
  }
  
  .advice-item {
    padding: 0.875rem;
  }
  
  .advice-icon {
    width: 36px;
    height: 36px;
    font-size: 1.125rem;
  }
}
</style> 