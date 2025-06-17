<template>
  <div>
    <h1 class="mb-4">刷脸签到</h1>
    <div class="card mb-4">
      <div class="card-header">视频流预览</div>
      <div class="card-body text-center">
        <div class="video-container">
          <img :src="eventBus.videoFeedUrl" alt="视频监控" class="video-feed">
          <div class="video-overlay" v-if="!eventBus.videoFeedUrl">
            <div class="loading-spinner"></div>
          </div>
        </div>
      </div>
    </div>
    <div class="text-center">
      <button class="btn btn-primary" @click="handleSignin" :disabled="buttonLoading">
        <span v-if="buttonLoading" class="spinner-border spinner-border-sm me-2"></span>
        刷脸签到
      </button>
    </div>
    <div v-if="result" class="alert mt-4" :class="result.success ? 'alert-success' : 'alert-danger'">
      {{ result.message }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import eventBus from '@/services/eventBus'
import { faceSignin } from '@/services/api.js'

const buttonLoading = ref(false);
const result = ref(null);
const handleSignin = async () => {
  buttonLoading.value = true;
  result.value = null;

  faceSignin(eventBus.currentMonitor)
    .then(response => {
      result.value = response.data;
    })
    .catch(error => {
      result.value = error.response?.data || {
        success: false,
        message: error.message || '签到失败，请稍后再试。'
      };
    })
    .finally(() => {
      buttonLoading.value = false;
    });
};

</script>

<style scoped>
.card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
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

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}
</style>