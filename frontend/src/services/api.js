import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/monitor/udpserver,0.0.0.0:8099/'
})

// 健康状态API
export function getStatus() {
  return api.get('/status')
}

// 健康指标历史数据API
export function getHealthMetrics(days = 7) {
  return api.get(`/health_metrics?days=${days}`)
}

// WebSocket连接
let ws = null
let reconnectTimer = null
let reconnectCount = 0
const MAX_RECONNECT = 5  // 最大重连次数
const RECONNECT_INTERVAL = 3000 // 3秒重连

export function connectWebSocket(onMessage, onClose) {
  // 如果已经连接，先关闭
  if (ws) {
    ws.close()
  }

  // 如果重连次数过多，不再重连
  if (reconnectCount >= MAX_RECONNECT) {
    console.error(`WebSocket重连失败次数过多(${reconnectCount}/${MAX_RECONNECT})，停止重连`);
    return;
  }

  // 创建WebSocket连接
  // 智能判断WebSocket连接地址
  let wsUrl;
  const hostname = window.location.hostname;
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';

  // 如果是本地开发环境，尝试通过Vite代理连接
  if (isLocalhost) {
    // 尝试通过Vite代理连接
    wsUrl = `ws://${hostname}:8000/monitor/udpserver,0.0.0.0:8099/ws`;
    console.log('使用本地开发环境WebSocket连接');
  } else {
    // 生产环境或局域网环境，直接连接到后端
    wsUrl = `ws://${hostname}:8000/monitor/udpserver,0.0.0.0:8099/ws`;
    console.log('使用生产环境WebSocket连接');
  }

  console.log(`正在连接WebSocket(${reconnectCount+1}/${MAX_RECONNECT+1}): ${wsUrl}`);
  
  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket连接已建立');
      // 连接成功后清除重连定时器和重连计数
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
      reconnectCount = 0;  // 重置重连计数
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (onMessage) {
          onMessage(data)
        }
      } catch (error) {
        console.error('解析WebSocket消息出错:', error)
      }
    }

    ws.onclose = (event) => {
      console.log('WebSocket连接已关闭:', event.code, event.reason)
      if (onClose) {
        onClose(event)
      }

      // 增加重连计数
      reconnectCount++;
      
      // 设置重连定时器
      if (reconnectCount <= MAX_RECONNECT) {
        reconnectTimer = setTimeout(() => {
          console.log(`尝试重新连接WebSocket(${reconnectCount}/${MAX_RECONNECT})...`);
          connectWebSocket(onMessage, onClose);
        }, RECONNECT_INTERVAL);
      } else {
        console.error(`WebSocket重连次数达到上限(${MAX_RECONNECT})，停止重连`);
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
    }
  } catch (error) {
    console.error('创建WebSocket连接出错:', error);
    // 增加重连计数
    reconnectCount++;
    // 设置重连定时器
    if (reconnectCount <= MAX_RECONNECT) {
      reconnectTimer = setTimeout(() => {
        console.log(`尝试重新连接WebSocket(${reconnectCount}/${MAX_RECONNECT})...`);
        connectWebSocket(onMessage, onClose);
      }, RECONNECT_INTERVAL);
    }
  }

  return {
    close: () => {
      if (ws) {
        ws.close()
      }
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
      reconnectCount = 0;  // 重置重连计数
    }
  }
} 