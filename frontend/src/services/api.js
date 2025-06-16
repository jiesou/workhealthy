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
  return cameraUrl.replace(/[:/]/g, ',')
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

// 获取指定摄像头的状态
export const getStatus = async (cameraUrl) => {
  try {
    if (cameraUrl) {
      // 斜杠和冒号在URL中替换为逗号
      const response = await apiClient.get(`/monitor/${encodeMonitorUrl(cameraUrl)}/status`)
      return response
    }
  } catch (error) {
    console.error('获取状态失败:', error)
    throw error
  }
}

// Add this function to the file
export const getWorkSessionHistory = async (cameraUrl, startDateTs, endDateTs) => {
  if (!cameraUrl) {
    console.error('Camera URL is required for fetching work session history');
    return { data: [] }; // Return empty data or throw error
  }
  try {
    const encodedCameraUrl = encodeMonitorUrl(cameraUrl); // Use existing utility
    const response = await apiClient.get(`/monitor/${encodedCameraUrl}/history`, { // Updated URL
      params: {
        start_date_ts: startDateTs,
        end_date_ts: endDateTs,
      },
    });
    return response.data; // The backend returns a list of sessions directly
  } catch (error) {
    console.error('获取工作会话历史数据出错:', error);
    throw error;
  }
};

// 连接指定摄像头的WebSocket
export const connectWebSocket = (onMessage, onClose, cameraUrl) => {
  let wsUrl
  if (cameraUrl) {
    wsUrl = `${WS_BASE_URL}/monitor/${encodeMonitorUrl(cameraUrl)}/ws`
  }
  
  const ws = new WebSocket(wsUrl)
  
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
    if (onClose) {
      onClose(event)
    }
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket错误:', error)
  }
  
  return ws
}