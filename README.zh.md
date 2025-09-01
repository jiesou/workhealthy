# WorkHealthy - 工位健康检测系统

这是一个使用计算机视觉（YOLO）和 LLM 来监测办公室白领工位健康状况的系统。它就像现实世界中的"屏幕使用时间"一样，可以根据工人的工作姿态、活动情况和饮水习惯，提供实时健康状态反馈和建议。

## 特性

- **实时健康监测**：跟踪工作姿态、活动频率和饮水习惯，还有配套智能插座，跟踪用电量（智能插座是原有的项目，尚未完全开源）
- **多摄像头支持**：一个上位机支持同时连接多个下位机设备
- **AI 智能分析**：使用 YOLO 计算机视觉模型进行人员检测和活动分析
- **LLM 集成**：提供智能健康建议和洞察
- **实时反馈**：基于 WebSocket 的实时通信和更新
- **嵌入式界面**：ESP32 设备上的 LVGL 用户界面
- **USB 图传**：使用 usb_stream 实现对 USB 摄像头的支持，同时使用 UDP 自拼包，实现高性能图传

## 架构

系统由两个主要组件组成：

### 上位机
- **前端**：Vue.js 应用，部分使用 Three.js 和 TresJS 进行 3D 可视化
- **后端**：FastAPI + SQLite 数据库
- **视频处理**：实时 YOLO 模型推理（YOLOv8、YOLO11）
- **健康分析**：智能监控和建议引擎
- **多路支持**：同时处理多个摄像头输入

### 下位机
支持两个版本的固件：

1. **ESP32-S3-LCD-EV-Board v1.5**：带 LCD 显示屏和 LVGL 界面的高级版本
2. **ESP-CAM**：紧凑型纯摄像头版本

两个固件都具有：
- PlatformIO Arduino/FreeRTOS 开发
- 使用 usb_stream 库的 USB 图传
- 与上位机的 WebSocket 通信
- 实时视频传输

## 硬件要求

### 上位机
- Docker

### 下位机设备
- **ESP32-S3-LCD-EV-Board v1.5** 或 **ESP-CAM**
- USB 数据线用于连接和供电
- 摄像头模块（两个板子都集成）

## 安装

使用 devcontainer

前端依赖 `yarn` 安装即可

后端需要编辑 `.env.example`

编辑 [`api/monitor.py`](https://github.com/jiesou/workhealthy/blob/d3066bf7cae3a1f2b7ac972445f81eb29522e923/backend/api/monitor.py#L22-L23) 注册所需的下位机摄像头。`current_sensor_url` 参数是连接未开源的 智能插座 的，可以不写

运行
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
在 devcontainer 的 venv 中安装 pip 依赖

然后 `python main.py` 来启动

### 访问应用
- **前端界面**：http://localhost:5173
- **后端 API**：http://localhost:8000

## 嵌入式固件刷入

1. 切换到对应目录的 `.code-workspace`（必须，否则 PlatformIO 不认项目）

2. 需要编辑上位机相关信息：

- 图传：[UDP_SERVER_IP](https://github.com/jiesou/workhealthy/blob/d3066bf7cae3a1f2b7ac972445f81eb29522e923/firmware-esp-lcd-ev/src/udp_client.cpp#L9C9-L9C22)
- WebSocket：[WS_SERVER_HOST](https://github.com/jiesou/workhealthy/blob/d3066bf7cae3a1f2b7ac972445f81eb29522e923/firmware-esp-lcd-ev/src/wsclient.cpp#L4)
- WiFi（MCU 作为 STA，需要提供外部 AP）：[ssid/password](https://github.com/jiesou/workhealthy/blob/d3066bf7cae3a1f2b7ac972445f81eb29522e923/firmware-esp-lcd-ev/src/main.cpp#L24)

3. Build，然后 `pio run --target upload` 即可

### 架构原则
- **胖服务端**：前后端沟通的核心是 websocket 里的 [`insights`](https://github.com/jiesou/workhealthy/blob/d3066bf7cae3a1f2b7ac972445f81eb29522e923/backend/monitor.py#L52-L102)。后端直接生成完整 insights message，前端不应该动态更新数据
- **不要 Overengineering**：保持代码实现简短简单，如果可能，减少代码的更改
- **多摄像头支持**：对多摄像头（多 monitor.py）的支持要格外留意
- **统一时间格式**：为了在嵌入式端更好操作。时间的数据类型统一采用 time.time() 转 int 的秒级时间戳，不使用 datetime
