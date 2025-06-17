import axios from 'axios'

// 设置基础URL
const API_BASE_URL = 'http://localhost:5173/api'
const WS_BASE_URL = 'ws://localhost:5173/api'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000
})

// Monitor URL 转模糊匹配工具函数
export const encodeMonitorUrl = (cameraUrl) => {
  if (!cameraUrl) return ''
  // 斜杠和冒号在URL中替换为逗号
  return cameraUrl.replace(/[:/]/g, '-')
}

// 获取摄像头列表
export const getMonitorList = async () => {
  try {
    const response = await apiClient.get('/monitor/list')
    return response.data
  } catch (error) {
    console.error('获取摄像头列表失败:', error)
    throw error
  }
}

// 健康指标历史数据API
export function getHealthMetrics(days = 7) {
  return apiClient.get(`/health_metrics?days=${days}`)
}

// Add this function to the file
export const getWorkSessionHistory = async (monitorUrl, startDateTs, endDateTs) => {
  if (!monitorUrl) {
    throw new Error('monitorUrl is required');
  }
  try {
    const response = await apiClient.get(`/monitor/${encodeMonitorUrl(monitorUrl)}/history`, { // Updated URL
      params: {
        start_date_ts: startDateTs,
        end_date_ts: endDateTs,
      },
    });
    return response.data;
  } catch (error) {
    console.error('获取工作会话历史数据出错:', error);
    throw error;
  }
};

export const faceSignin = async(monitorUrl) => {
  if (!monitorUrl) {
    console.error('monitorUrl is required for face signin')
    return
  }
  return apiClient.post(`/monitor/${encodeMonitorUrl(monitorUrl)}/face_signin`);
}

// 连接指定摄像头的WebSocket
export const connectWebSocket = (onMessage, video_url) => {
  if (!video_url) {
    console.error('视频URL不能为空，无法建立WebSocket连接')
    return;
  }
  console.log('建立WebSocket连接:', `${WS_BASE_URL}/monitor/${encodeMonitorUrl(video_url)}/ws`)
  const ws = new WebSocket(`${WS_BASE_URL}/monitor/${encodeMonitorUrl(video_url)}/ws`)
  
  ws.onopen = () => {
    console.log('WebSocket连接已建立')
  }
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage(data)
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }
  
  ws.onclose = (event) => {
    console.log('WebSocket连接已关闭')
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket错误:', error)
  }
  
  return ws
}