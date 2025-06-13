<template>
  <div class="app-container">
    <header class="navbar navbar-dark bg-dark">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">
          工位健康检测系统
        </router-link>
        <div class="navbar-nav ms-auto">
          <div class="dropdown">
            <button class="btn btn-outline-light dropdown-toggle" type="button" id="cameraDropdown" data-bs-toggle="dropdown" aria-expanded="false">
              <i class="bi bi-camera-video me-2"></i>
              {{ currentCameraDisplay }}
            </button>
            <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="cameraDropdown">
              <li v-for="camera in cameraList" :key="camera" 
                  @click="selectCamera(camera)"
                  :class="{ active: camera === currentCamera }">
                <a class="dropdown-item" href="#">
                  <i class="bi bi-camera-video me-2"></i>
                  {{ camera }}
                </a>
              </li>
              <li><hr class="dropdown-divider"></li>
              <li @click="refreshCameraList">
                <a class="dropdown-item" href="#">
                  <i class="bi bi-arrow-clockwise me-2"></i>
                  刷新列表
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </header>
    
    <div class="container-fluid">
      <div class="row">
        <div class="col-md-2 sidebar p-0">
          <nav class="nav flex-column">
            <router-link class="sidebar-link" to="/" :class="{ active: $route.path === '/' }">
              <i class="bi bi-speedometer2 me-2"></i> 实时监控
            </router-link>
            <router-link class="sidebar-link" to="/history" :class="{ active: $route.path === '/history' }">
              <i class="bi bi-graph-up me-2"></i> 历史数据
            </router-link>
            <router-link class="sidebar-link" to="/settings" :class="{ active: $route.path === '/settings' }">
              <i class="bi bi-gear me-2"></i> 系统设置
            </router-link>
            <router-link class="sidebar-link" to="/face-signin" :class="{ active: $route.path === '/face-signin' }">
              <i class="bi bi-person-bounding-box me-2"></i> 刷脸签到
            </router-link>
          </nav>
        </div>
        
        <div class="col-md-10 p-4">
          <router-view />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getMonitorList } from '@/services/api'
import eventBus from '@/services/eventBus'

export default {
  name: 'App',
  data() {
    return {
      cameraList: [],
      currentCamera: null
    }
  },
  computed: {
    currentCameraDisplay() {
      if (!this.currentCamera) return '选择摄像头'
      return this.currentCamera
    }
  },
  methods: {
    async loadCameraList() {
      try {
        this.cameraList = await getMonitorList()
        // 如果没有选中的摄像头且列表不为空，选择第一个
        if (!this.currentCamera && this.cameraList.length > 0) {
          this.selectCamera(this.cameraList[0])
        }
        console.log('摄像头列表加载成功:', this.cameraList)
      } catch (error) {
        console.error('加载摄像头列表失败:', error)
      }
    },
    selectCamera(camera) {
      this.currentCamera = camera
      // 使用事件总线通知其他组件摄像头已切换
      eventBus.setCurrentCamera(camera)
    },
    async refreshCameraList() {
      await this.loadCameraList()
    }
  },
  async mounted() {
    await this.loadCameraList()
  }
}
</script>

<style>
@import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css");
</style>