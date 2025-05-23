<template>
  <div class="card">
    <div class="card-header">健康建议</div>
    <div class="card-body">
      <div v-if="!metrics" class="text-center">
        <p>暂无健康数据</p>
      </div>
      <div v-else>
        <ul class="list-group list-group-flush">
          <li class="list-group-item ps-0 border-0" v-if="!metrics.cup_detected">
            <i class="bi bi-cup-straw me-2 text-warning"></i>
            <strong>补水建议：</strong> 记得喝水，保持水分充足。
          </li>
          <li class="list-group-item ps-0 border-0" v-if="!metrics.is_active">
            <i class="bi bi-activity me-2 text-warning"></i>
            <strong>活动建议：</strong> 建议起身活动，避免久坐。
          </li>
        </ul>
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