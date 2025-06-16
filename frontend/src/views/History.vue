<template>
  <div v-if="!currentMonitor" class="text-center py-5">
    <i class="bi bi-camera-video-off fs-1 text-muted"></i>
    <p class="mt-2">请先在仪表盘页面选择一个监控摄像头。</p>
  </div>
  <div v-else>
    <h1 class="mb-4">工作历史记录</h1>
    
    <div class="card mb-4">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span>每日工作时长</span>
        <div>
          <select v-model="selectedDays" class="form-select form-select-sm" @change="fetchWorkSessionHistoryMethod">
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
        <div v-else-if="!hasWorkSessions" class="text-center py-5">
          <i class="bi bi-exclamation-circle fs-1 text-muted"></i>
          <p class="mt-2">暂无历史数据</p>
        </div>
        <div v-else>
          <canvas ref="chartCanvasRef" height="300"></canvas> <!-- Changed ref name -->
        </div>
      </div>
    </div>
    
    <div class="card">
      <div class="card-header">
        工作会话详情
      </div>
      <div class="card-body p-0">
        <div v-if="loading && !hasWorkSessions" class="text-center py-5"> <!-- Show loading only if no data yet -->
          <div class="spinner-border" role="status">
            <span class="visually-hidden">加载中...</span>
          </div>
          <p class="mt-2">正在加载数据...</p>
        </div>
        <div v-else-if="!hasWorkSessions" class="text-center py-5">
          <i class="bi bi-exclamation-circle fs-1 text-muted"></i>
          <p class="mt-2">暂无历史数据</p>
        </div>
        <div v-else class="table-responsive">
          <table class="table table-hover mb-0">
            <thead>
              <tr>
                <th>开始时间</th>
                <th>结束时间</th>
                <th>时长</th>
                <th>监控ID</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="session in workSessionsRaw" :key="session.id">
                <td>{{ formatDateTime(session.start_time) }}</td>
                <td>{{ formatDateTime(session.end_time) }}</td>
                <td>{{ formatDuration(session.duration_seconds) }}</td>
                <td>{{ session.monitor_video_url }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { getWorkSessionHistory } from '@/services/api';
import eventBus from '@/services/eventBus';
import Chart from 'chart.js/auto';

const workSessionsRaw = ref([]);
const currentMonitor = ref(eventBus.currentCamera || null);
const loading = ref(true);
const selectedDays = ref('7'); // Default to 7 days
const chartCanvasRef = ref(null); // Ref for the canvas element
let chartInstance = null; // To hold the chart instance

const hasWorkSessions = computed(() => workSessionsRaw.value && workSessionsRaw.value.length > 0);

const dailyAggregatedData = computed(() => {
  if (!workSessionsRaw.value || workSessionsRaw.value.length === 0) {
    return { labels: [], data: [] };
  }
  const dailyTotals = {}; // Key: 'YYYY-MM-DD', Value: total duration in seconds
  workSessionsRaw.value.forEach(session => {
    if (session.start_time === null || session.start_time === undefined) return;
    const date = new Date(session.start_time * 1000);
    const dayKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    if (!dailyTotals[dayKey]) {
      dailyTotals[dayKey] = 0;
    }
    dailyTotals[dayKey] += session.duration_seconds || 0;
  });

  const labels = Object.keys(dailyTotals).sort(); // Sort dates
  const data = labels.map(label => parseFloat((dailyTotals[label] / 3600).toFixed(2))); // Convert seconds to hours

  return { labels, data };
});

const fetchWorkSessionHistoryMethod = async () => {
  if (!eventBus.currentMonitor) {
    console.log('No monitor selected, skipping fetch for work session history.');
    workSessionsRaw.value = []; // Clear data if no monitor
    loading.value = false;
    initOrUpdateChart(); // Attempt to clear or update chart
    return;
  }
  loading.value = true;
  try {
    const endDateTs = Math.floor(Date.now() / 1000);
    const startDateTs = endDateTs - (parseInt(selectedDays.value) * 24 * 60 * 60);
    const sessions = await getWorkSessionHistory(eventBus.currentMonitor, startDateTs, endDateTs);
    workSessionsRaw.value = sessions; // API returns array directly
  } catch (error) {
    console.error('获取工作会话历史数据出错:', error);
    workSessionsRaw.value = []; // Clear data on error
  } finally {
    loading.value = false;
    initOrUpdateChart();
  }
};

const initOrUpdateChart = () => {
  if (!chartCanvasRef.value) return; // Canvas not ready

  const { labels, data } = dailyAggregatedData.value;

  if (chartInstance) {
    chartInstance.destroy(); // Destroy previous instance before creating new one
  }

  if (!labels.length && !data.length && workSessionsRaw.value.length === 0 ) {
     // if no data at all, don't try to render an empty chart
    return;
  }


  chartInstance = new Chart(chartCanvasRef.value.getContext('2d'), {
    type: 'bar', // Changed to bar for better daily representation
    data: {
      labels: labels,
      datasets: [
        {
          label: '工作时长 (小时)',
          data: data,
          borderColor: '#007bff',
          backgroundColor: 'rgba(0, 123, 255, 0.5)',
          borderWidth: 2,
          borderRadius: 5, // Rounded bars
          barPercentage: 0.6, // Bar width
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: '每日工作时长趋势',
          font: { size: 16 }
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || '';
              if (label) {
                label += ': ';
              }
              if (context.parsed.y !== null) {
                label += context.parsed.y + ' 小时';
              }
              return label;
            }
          }
        },
        legend: {
          display: true, // Keep legend for clarity
          position: 'top',
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: '工作时长 (小时)'
          },
          suggestedMax: Math.max(...(data.length > 0 ? data : [8]), 8) // Dynamic max based on data or 8 hours
        },
        x: {
          title: {
            display: true,
            text: '日期'
          },
          grid: {
            display: false // Hide X-axis grid lines for cleaner look
          }
        }
      }
    }
  });
};

const formatDateTime = (timestamp) => {
  if (timestamp === null || timestamp === undefined) return 'N/A';
  const date = new Date(timestamp * 1000);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
};

const formatDuration = (totalSeconds) => {
  if (totalSeconds === null || totalSeconds === undefined || totalSeconds < 0) return 'N/A';
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  let result = '';
  if (h > 0) result += `${h}h `;
  if (m > 0 || (h > 0 && m === 0)) result += `${m}m `; // Show minutes if hours are present or if minutes > 0
  result += `${s}s`;
  return result.trim() || '0s'; // Ensure "0s" if duration is 0
};

let cameraChangeHandler;

onMounted(() => {
  // fetchWorkSessionHistoryMethod will be called by the watcher if currentMonitor is already set.
  // If currentMonitor is null, the v-if in template handles it.
  // If currentMonitor is set, watcher on currentMonitor will trigger fetch.
  if (eventBus.currentMonitor) {
    fetchWorkSessionHistoryMethod();
  }

  cameraChangeHandler = (newCamera) => {
    eventBus.currentMonitor = newCamera;
    // fetchWorkSessionHistoryMethod will be called by the watcher on currentMonitor
  };
  eventBus.on('camera-changed', cameraChangeHandler);
});

onBeforeUnmount(() => {
  if (cameraChangeHandler) {
    eventBus.off('camera-changed', cameraChangeHandler);
  }
  if (chartInstance) {
    chartInstance.destroy();
  }
});

watch(selectedDays, fetchWorkSessionHistoryMethod);
watch(currentMonitor, (newValue, oldValue) => {
  if (newValue !== oldValue) { // only fetch if monitor actually changed
    fetchWorkSessionHistoryMethod();
  }
}, { immediate: false }); // immediate: false, as onMounted handles initial if needed

</script>

<style scoped>
.card {
  border-radius: 0.75rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.card-header {
  background-color: #f8f9fa;
  font-weight: 600;
  padding: 1rem 1.25rem;
}
.table-hover tbody tr:hover {
  background-color: #e9ecef;
}
/* Add styles for the message when no monitor is selected */
.text-center.py-5 i.bi {
  font-size: 3rem; /* Larger icon */
  color: #6c757d; /* Muted color */
}
.text-center.py-5 p {
  font-size: 1.1rem;
  color: #495057;
}
</style>