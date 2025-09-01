import uvicorn
import os
import signal
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class MyServer(uvicorn.Server):
    """自定义Server，处理退出信号"""
    
    def install_signal_handlers(self):
        """重写信号处理器安装方法"""
        signal.signal(signal.SIGINT, self.force_exit)
    
    def force_exit(self):
        """强制退出处理器"""
        os._exit(1)

def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "True").lower() == "true"
    
    # 设置视频代理URL环境变量，默认使用本地代理服务器
    if not os.getenv("VIDEO_URL"):
        video_proxy_url = os.getenv("VIDEO_PROXY_URL", "http://localhost:8081/mjpeg")
        os.environ["VIDEO_URL"] = video_proxy_url
        print(f"使用视频代理服务器: {video_proxy_url}")
    
    # 启动FastAPI应用，确保启用WebSocket支持
    print("=== 正在启动后端服务")
    
    server = MyServer(uvicorn.Config(
        "backend.api:app",
        host=host,
        port=port,
        reload=reload,
        ws_ping_interval=20,
        ws_ping_timeout=30,
        log_level="info",
        access_log=True
    ))
    server.run()

if __name__ == "__main__":
    main()
