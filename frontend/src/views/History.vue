<template>
  <div>
    <h1 class="mb-4">历史健康数据</h1>
    
    <div class="card mb-4">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span>健康指标历史趋势</span>
        <div>
          <select v-model="selectedDays" class="form-select form-select-sm" @change="fetchHealthMetrics">
            <option value="7">近7天</option>
            <option value="14">近14天</option>
            <option value="30">近30天</option>
          </select>
        </div>
      </div>
      <div class="card-body">
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">加载中...</span>
          </div>
          <p class="mt-2">正在加载数据...</p>
        </div>
        <div v-else-if="!hasData" class="text-center py-5">
          <i class="bi bi-exclamation-circle fs-1 text-muted"></i>
          <p class="mt-2">暂无历史数据</p>
        </div>
        <div v-else>
          <canvas ref="chart" height="300"></canvas>
        </div>
      </div>
    </div>
    
    <div class="card">
      <div class="card-header">
        历史数据列表
      </div>
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">加载中...</span>
          </div>
          <p class="mt-2">正在加载数据...</p>
        </div>
        <div v-else-if="!hasData" class="text-center py-5">
          <i class="bi bi-exclamation-circle fs-1 text-muted"></i>
          <p class="mt-2">暂无历史数据</p>
        </div>
        <div v-else class="table-responsive">
          <table class="table table-hover mb-0">
            <thead>
              <tr>
                <th>日期时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in metricsData" :key="item.id">
                <td>{{ formatDateTime(item.timestamp) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getHealthMetrics } from '@/services/api'
import Chart from 'chart.js/auto'

export default {
  name: 'History',
  data() {
    return {
      loading: true,
      metricsData: [],
      selectedDays: '7',
      chart: null
    }
  },
  computed: {
    hasData() {
      return this.metricsData && this.metricsData.length > 0
    }
  },
  methods: {
    async fetchHealthMetrics() {
      this.loading = true
      try {
        const response = await getHealthMetrics(this.selectedDays)
        this.metricsData = response.data
        this.initChart()
      } catch (error) {
        console.error('获取健康指标历史数据出错:', error)
      } finally {
        this.loading = false
      }
    },
    
    initChart() {
      if (!this.hasData) return
      
      // 准备数据
      const dates = this.metricsData.map(item => this.formatDate(item.timestamp))
      
      // 销毁旧图表
      if (this.chart) {
        this.chart.destroy()
      }
      
      // 创建新图表
      const ctx = this.$refs.chart.getContext('2d')
      this.chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: dates,
          datasets: [
            {
              label: '健康指标趋势',
              data: this.metricsData.map(item => item.overall_health_score),
              borderColor: '#ff9f40',
              backgroundColor: 'rgba(255, 159, 64, 0.1)',
              tension: 0.1,
              fill: false,
              borderWidth: 2
            }
          ]
        },
        options: {
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: '健康指标趋势'
            },
            tooltip: {
              mode: 'index',
              intersect: false
            }
          },
          scales: {
            y: {
              min: 0,
              max: 100,
              title: {
                display: true,
                text: '评分'
              }
            },
            x: {
              title: {
                display: true,
                text: '日期'
              }
            }
          }
        }
      })
    },
    
    formatDate(dateString) {
      const date = new Date(dateString)
      return `${date.getMonth() + 1}/${date.getDate()}`
    },
    
    formatDateTime(dateString) {
      const date = new Date(dateString)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    }
  },
  mounted() {
    this.fetchHealthMetrics()
  }
}
</script> 