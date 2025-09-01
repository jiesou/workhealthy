<template>
  <div class="status-card" :class="type">
    <div class="card-content">
      <div class="icon-wrapper">
        <i :class="iconClass"></i>
      </div>
      <div class="text-content">
        <h3 class="card-title">{{ title }}</h3>
        <p class="status-text" :class="statusClass" v-html="status"></p>
        <p class="description">{{ description }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatusCard',
  props: {
    title: {
      type: String,
      required: true
    },
    status: {
      type: String,
      required: true
    },
    description: {
      type: String,
      default: ''
    },
    icon: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: 'info',
      validator: (value) => ['success', 'warning', 'danger', 'info'].includes(value)
    }
  },
  computed: {
    iconClass() {
      return {
        'bi-person-check': this.icon === 'person',
        'bi-activity': this.icon === 'activity',
        'bi-cup-hot': this.icon === 'cup',
        'bi-clock-history': this.icon === 'time',
        'bi-lightning': this.icon === 'current',
        'text-success': this.type === 'success',
        'text-warning': this.type === 'warning',
        'text-danger': this.type === 'danger',
        'text-info': this.type === 'info'
      }
    },
    statusClass() {
      return {
        'text-success': this.type === 'success',
        'text-warning': this.type === 'warning',
        'text-danger': this.type === 'danger',
        'text-info': this.type === 'info'
      }
    }
  }
}
</script>

<style scoped>
.status-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 1.5rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.status-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.card-content {
  display: flex;
  align-items: flex-start;
  gap: 1.25rem;
}

.icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.status-card.success .icon-wrapper {
  background: rgba(52, 199, 89, 0.1);
  color: #34c759;
}

.status-card.warning .icon-wrapper {
  background: rgba(255, 204, 0, 0.1);
  color: #ffcc00;
}

.status-card.danger .icon-wrapper {
  background: rgba(255, 69, 58, 0.1);
  color: #ff453a;
}

.status-card.info .icon-wrapper {
  background: rgba(0, 122, 255, 0.1);
  color: #007aff;
}

.text-content {
  flex: 1;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0 0 0.5rem 0;
}

.status-text {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

.description {
  font-size: 0.875rem;
  color: #86868b;
  margin: 0;
  line-height: 1.4;
}

.status-text.success {
  color: #34c759;
}

.status-text.warning {
  color: #ffcc00;
}

.status-text.danger {
  color: #ff453a;
}

.status-text.info {
  color: #007aff;
}

@media (max-width: 768px) {
  .status-card {
    padding: 1.25rem;
  }
  
  .icon-wrapper {
    width: 40px;
    height: 40px;
    font-size: 1.25rem;
  }
  
  .card-title {
    font-size: 0.875rem;
  }
  
  .status-text {
    font-size: 1.125rem;
  }
  
  .description {
    font-size: 0.8125rem;
  }
}
</style> 