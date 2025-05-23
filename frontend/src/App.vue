<template>
  <div class="app-container">
    <header class="navbar navbar-dark bg-dark">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">
          工位健康检测系统
        </router-link>
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
export default {
  name: 'App'
}
</script>

<style>
@import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css");
</style> 