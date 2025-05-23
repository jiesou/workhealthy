#!/usr/bin/env python
import os
import sys
import time
import webbrowser
import threading
import subprocess
import platform
import signal

def start_video_proxy():
    """启动异步视频代理服务器（网络流模式）"""
    print("正在启动异步视频代理服务器...")
    try:
        # 启动异步代理，指定网络流源
        cmd = [sys.executable, "video_proxy_async.py", "--source", "http://192.168.4.1:81/stream"]
        if platform.system() == "Windows":
            proxy_process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            proxy_process = subprocess.Popen(cmd)
        return proxy_process
    except Exception as e:
        print(f"启动异步视频代理服务器失败: {e}")
        return None

def start_backend():
    """启动后端服务"""
    print("正在启动后端服务...")
    try:
        # 使用Python执行main.py
        if platform.system() == "Windows":
            backend_process = subprocess.Popen([sys.executable, "main.py"],
                                             creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            backend_process = subprocess.Popen([sys.executable, "main.py"])
        return backend_process
    except Exception as e:
        print(f"启动后端服务失败: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    print("正在启动前端服务...")
    try:
        os.chdir("frontend")
        # 检查前端依赖是否已安装
        if not os.path.exists("node_modules"):
            print("正在安装前端依赖...")
            if platform.system() == "Windows":
                subprocess.call("npm install", shell=True)
            else:
                subprocess.call("npm install", shell=True)
        
        # 启动前端开发服务器，添加 --host 0.0.0.0 参数
        if platform.system() == "Windows":
            frontend_process = subprocess.Popen("npm run dev -- --host 0.0.0.0", shell=True,
                                               creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            frontend_process = subprocess.Popen("npm run dev -- --host 0.0.0.0", shell=True)
        
        os.chdir("..")  # 返回上一级目录
        return frontend_process
    except Exception as e:
        print(f"启动前端服务失败: {e}")
        os.chdir("..")  # 确保返回上一级目录
        return None

def open_browser():
    """打开浏览器访问应用"""
    time.sleep(5)  # 等待服务启动
    print("正在打开浏览器...")
    webbrowser.open("http://localhost:5173")

if __name__ == "__main__":
    try:
        # 启动视频代理
        proxy_process = start_video_proxy()
        if not proxy_process:
            print("视频代理服务器启动失败，程序退出")
            sys.exit(1)
        
        # 等待视频代理启动
        print("等待视频代理服务器启动...")
        time.sleep(2)
        
        # 启动后端
        backend_process = start_backend()
        if not backend_process:
            print("后端服务启动失败，程序退出")
            proxy_process.terminate()
            sys.exit(1)
        
        # 启动前端
        frontend_process = start_frontend()
        if not frontend_process:
            print("前端服务启动失败，程序退出")
            backend_process.terminate()
            proxy_process.terminate()
            sys.exit(1)
        
        # 启动浏览器线程
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        print("工位健康检测系统已启动")
        print("视频代理服务器地址: http://localhost:8081")
        print("后端API地址: http://localhost:8000")
        print("前端界面地址: http://localhost:5173")
        print("按Ctrl+C停止服务...")
        
        # 等待用户中断
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n正在关闭服务...")
        
        if 'frontend_process' in locals():
            frontend_process.terminate()
        
        if 'backend_process' in locals():
            backend_process.terminate()
            
        if 'proxy_process' in locals():
            proxy_process.terminate()
        
        print("服务已关闭")
    except Exception as e:
        print(f"发生错误: {e}")
        
        if 'frontend_process' in locals():
            frontend_process.terminate()
        
        if 'backend_process' in locals():
            backend_process.terminate()
            
        if 'proxy_process' in locals():
            proxy_process.terminate() 