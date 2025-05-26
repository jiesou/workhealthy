<template>
  <div>
    <h1 class="mb-4">系统设置</h1>
    
    <div class="row">
      <div class="col-md-6">
        <div class="card mb-4">
          <div class="card-header">
            视频设置
          </div>
          <div class="card-body">
            <form @submit.prevent="saveVideoSettings">
              <div class="mb-3">
                <label for="videoUrl" class="form-label">视频流URL</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="videoUrl" 
                  v-model="settings.videoUrl"
                  placeholder="例如: http://127.0.0.1/api/video_feed"
                >
                <div class="form-text">输入摄像头提供的视频流URL地址，前端直接显示</div>
              </div>
              
              <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="enableVideoProcessing" v-model="settings.enableVideoProcessing">
                <label class="form-check-label" for="enableVideoProcessing">启用视频处理</label>
              </div>
              
              <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="enableYoloProcessing" v-model="settings.enableYoloProcessing" @change="toggleYoloProcessing">
                <label class="form-check-label" for="enableYoloProcessing">启用YOLO对象检测（禁用可提高前端视频流速度）</label>
              </div>
              
              <button type="submit" class="btn btn-primary">保存视频设置</button>
            </form>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header">
            检测设置
          </div>
          <div class="card-body">
            <form @submit.prevent="saveDetectionSettings">
              <div class="mb-3">
                <label for="detectionInterval" class="form-label">检测间隔 (秒)</label>
                <input 
                  type="number" 
                  class="form-control" 
                  id="detectionInterval" 
                  v-model="settings.detectionInterval"
                  min="1" 
                  max="60"
                >
              </div>
              
              <div class="mb-3">
                <label for="confidenceThreshold" class="form-label">检测置信度阈值</label>
                <input 
                  type="range" 
                  class="form-range" 
                  id="confidenceThreshold" 
                  v-model="settings.confidenceThreshold"
                  min="0" 
                  max="1" 
                  step="0.05"
                >
                <div class="text-end">{{ settings.confidenceThreshold }}</div>
              </div>
              
              <button type="submit" class="btn btn-primary">保存检测设置</button>
            </form>
          </div>
        </div>
      </div>
      
      <div class="col-md-6">
        <div class="card mb-4">
          <div class="card-header">
            健康指标设置
          </div>
          <div class="card-body">
            <form @submit.prevent="saveHealthSettings">
              <div class="mb-3">
                <label for="inactiveThreshold" class="form-label">不活动警告阈值 (分钟)</label>
                <input 
                  type="number" 
                  class="form-control" 
                  id="inactiveThreshold" 
                  v-model="settings.inactiveThreshold"
                  min="1" 
                  max="60"
                >
                <div class="form-text">超过该时间未检测到活动将发出警告</div>
              </div>
              
              <div class="mb-3">
                <label for="waterReminderInterval" class="form-label">喝水提醒间隔 (分钟)</label>
                <input 
                  type="number" 
                  class="form-control" 
                  id="waterReminderInterval" 
                  v-model="settings.waterReminderInterval"
                  min="15" 
                  max="120"
                >
                <div class="form-text">多长时间未检测到水杯将发出喝水提醒</div>
              </div>
              
              <div class="mb-3">
                <label for="workDurationWarningThreshold" class="form-label">工作时长警告阈值 (分钟)</label>
                <input 
                  type="number" 
                  class="form-control" 
                  id="workDurationWarningThreshold" 
                  v-model="settings.workDurationWarningThreshold"
                  min="30" 
                  max="240"
                >
                <div class="form-text">超过该时长将提醒休息</div>
              </div>
              
              <button type="submit" class="btn btn-primary">保存健康设置</button>
            </form>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header">
            系统信息
          </div>
          <div class="card-body">
            <ul class="list-group list-group-flush">
              <li class="list-group-item d-flex justify-content-between align-items-center">
                后端状态
                <span class="badge bg-success rounded-pill">运行中</span>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center">
                WebSocket连接
                <span class="badge bg-success rounded-pill">已连接</span>
              </li>
              <li class="list-group-item d-flex justify-content-between align-items-center">
                工位健康检测系统版本
                <span>v1.0.0</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Settings',
  data() {
    return {
      settings: {
        videoUrl: 'http://127.0.0.1/api/video_feed',
        enableVideoProcessing: true,
        enableYoloProcessing: true,
        detectionInterval: 5,
        confidenceThreshold: 0.5,
        inactiveThreshold: 15,
        waterReminderInterval: 60,
        workDurationWarningThreshold: 120
      },
      showSuccessAlert: false
    }
  },
  mounted() {
    // 从本地存储加载设置
    const savedSettings = localStorage.getItem('workHealthySettings')
    if (savedSettings) {
      try {
        this.settings = { ...this.settings, ...JSON.parse(savedSettings) }
      } catch (e) {
        console.error('解析保存的设置失败:', e)
      }
    }
  },
  methods: {
    saveVideoSettings() {
      this.saveSettings()
      // 这里可以添加将设置发送到后端的逻辑
      this.showSuccessMessage('视频设置已保存')
    },
    
    saveDetectionSettings() {
      this.saveSettings()
      this.showSuccessMessage('检测设置已保存')
    },
    
    saveHealthSettings() {
      this.saveSettings()
      this.showSuccessMessage('健康指标设置已保存')
    },
    
    saveSettings() {
      // 保存到本地存储
      localStorage.setItem('workHealthySettings', JSON.stringify(this.settings))
    },
    
    showSuccessMessage(message) {
      // 显示成功提示
      alert(message)
    },
    
    async toggleYoloProcessing() {
      try {
        const response = await fetch(`/api/toggle_yolo/${this.settings.enableYoloProcessing}`);
        const result = await response.json();
        if (result.status === 'success') {
          console.log(`YOLO处理已${this.settings.enableYoloProcessing ? '启用' : '禁用'}`);
        } else {
          console.error('切换YOLO处理失败:', result.message);
          // 如果失败，回滚设置
          this.settings.enableYoloProcessing = !this.settings.enableYoloProcessing;
        }
      } catch (error) {
        console.error('切换YOLO处理出错:', error);
        // 如果出错，回滚设置
        this.settings.enableYoloProcessing = !this.settings.enableYoloProcessing;
      }
    }
  }
}
</script> 