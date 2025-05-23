<template>
  <div class="card">
    <div class="card-header">
      {{ title }}
    </div>
    <div class="card-body text-center">
      <i :class="iconClass" class="bi fs-1 mb-3"></i>
      <h5 class="card-title" :class="statusClass">{{ status }}</h5>
      <p class="card-text">{{ description }}</p>
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