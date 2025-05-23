<template>
  <div>
    <h1 class="mb-4">刷脸签到</h1>
    <div class="card mb-4">
      <div class="card-header">视频流预览</div>
      <div class="card-body text-center">
        <!-- MJPEG流预览 -->
        <img ref="videoImg" :src="videoUrl" alt="视频流" class="img-fluid rounded" style="max-height: 400px;" crossorigin="anonymous" />
      </div>
    </div>
    <div class="text-center">
      <button class="btn btn-primary" @click="handleSignin" :disabled="loading">
        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
        刷脸签到
      </button>
    </div>
    <div v-if="result" class="alert mt-4" :class="result.success ? 'alert-success' : 'alert-danger'">
      {{ result.message }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'FaceSignin',
  data() {
    return {
      loading: false, // 按钮加载状态
      result: null,   // 签到结果
      videoUrl: ''    // 视频流地址
    }
  },
  mounted() {
    this.loadVideoUrl();
  },
  methods: {
    /**
     * 加载视频流地址，与Dashboard保持一致
     */
    loadVideoUrl() {
      // 可根据实际情况从本地存储或配置获取
      const savedSettings = localStorage.getItem('workHealthySettings');
      if (savedSettings) {
        try {
          const settings = JSON.parse(savedSettings);
          if (settings.videoProxyUrl) {
            this.videoUrl = settings.videoProxyUrl;
            return;
          }
        } catch (e) {
          // 忽略解析错误
        }
      }
      // 默认地址
      this.videoUrl = 'http://localhost:8081/mjpeg';
    },
    /**
     * 采集当前MJPEG流画面并上传签到
     */
    async handleSignin() {
      this.loading = true;
      this.result = null;
      try {
        // 获取img元素
        const img = this.$refs.videoImg;
        // 创建canvas并绘制当前帧
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth || img.width;
        canvas.height = img.naturalHeight || img.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        // 转为blob
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
        // 构造FormData上传
        const formData = new FormData();
        formData.append('image', blob, 'capture.jpg');
        // 调用后端接口
        const resp = await fetch('/api/face_signin', {
          method: 'POST',
          body: formData
        });
        const data = await resp.json();
        this.result = data;
      } catch (err) {
        this.result = { success: false, message: '签到失败: ' + err.message };
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
.card {
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
</style> 