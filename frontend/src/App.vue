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
              <li v-for="monitor in eventBus.monitorList" :key="monitor" 
                  @click="eventBus.currentMonitor = monitor"
                  :class="{ active: monitor === eventBus.currentMonitor }">
                <a class="dropdown-item" href="#">
                  <i class="bi bi-camera-video me-2"></i>
                  {{ monitor }}
                </a>
              </li>
              <li><hr class="dropdown-divider"></li>
              <li>
                <router-link class="dropdown-item" to="/monitors-overview">
                  <i class="bi bi-camera-video me-2"></i>
                  监控总览
                </router-link>
              </li>
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

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getMonitorList } from '@/services/api'
import eventBus from '@/services/eventBus'

const route = useRoute()

const currentCameraDisplay = computed(() => {
  if (!eventBus.currentMonitor) return '选择摄像头'
  return eventBus.currentMonitor
})

async function loadCameraList() {
  try {
    eventBus.monitorList = await getMonitorList()
    if (!eventBus.currentMonitor && eventBus.monitorList.length > 0) {
      eventBus.currentMonitor = eventBus.monitorList[0]
    }
    console.log('摄像头列表加载成功:', eventBus.monitorList)
  } catch (error) {
    console.error('加载摄像头列表失败:', error)
  }
}

async function refreshCameraList() {
  await loadCameraList()
}

onMounted(async () => {
  await loadCameraList()
})
</script>

<style>
@import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.1/font/bootstrap-icons.css");
</style>
