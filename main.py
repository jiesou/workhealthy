import uvicorn
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

if __name__ == "__main__":
    # 获取配置，默认为开发环境配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "True").lower() == "true"
    
    # 设置视频代理URL环境变量，默认使用本地代理服务器
    if not os.getenv("VIDEO_URL"):
        video_proxy_url = os.getenv("VIDEO_PROXY_URL", "http://localhost:8081/mjpeg")
        os.environ["VIDEO_URL"] = video_proxy_url
        print(f"使用视频代理服务器: {video_proxy_url}")
    
    # 启动FastAPI应用，确保启用WebSocket支持
    print("=== 正在启动后端服务，WebSocket端点: ws://" + host + ":" + str(port) + "/ws")
    uvicorn.run(
        "backend.api:app", 
        host=host, 
        port=port, 
        reload=reload, 
        ws_ping_interval=20, 
        ws_ping_timeout=30,
        log_level="info",
        access_log=True
    )