# WorkHealthy - 工位健康检测系统

这是一个使用计算机视觉（YOLO）和 LLM 来监测办公室白领工位健康状况的系统。它就像现实世界中的"屏幕使用时间"一样，可以根据工人的工作姿态、活动情况和饮水习惯，提供实时健康状态反馈和建议。

## 🎯 系统特性

- **实时健康监测**：跟踪工作姿态、活动频率和饮水习惯
- **多摄像头支持**：一个上位机支持同时连接多个下位机设备
- **AI 智能分析**：使用 YOLO 计算机视觉模型进行人员检测和活动分析
- **LLM 集成**：提供智能健康建议和洞察
- **实时反馈**：基于 WebSocket 的实时通信和更新
- **嵌入式界面**：ESP32 设备上的 LVGL 用户界面
- **USB 图传**：使用 usb_stream 库实现高性能视频传输

## 🏗️ 系统架构

系统由两个主要组件组成：

### 上位机
- **前端**：Vue.js 应用，使用 Three.js 和 TresJS 进行 3D 可视化
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

## 🔧 硬件要求

### 上位机
- Python 3.8+
- Node.js 14+
- USB 端口用于连接嵌入式设备
- 推荐使用 GPU 以加速 YOLO 推理

### 下位机设备
- **ESP32-S3-LCD-EV-Board v1.5** 或 **ESP-CAM**
- USB 数据线用于连接和供电
- 摄像头模块（两个板子都集成）

## 📦 安装配置

### 1. 克隆仓库
```bash
git clone https://github.com/jiesou/workhealthy.git
cd workhealthy
```

### 2. 设置 Python 环境
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 设置前端依赖
```bash
cd frontend
npm install
cd ..
```

### 4. 配置环境变量
```bash
cp env.example .env
```

根据您的设置编辑 `.env` 文件：
```env
# 服务器配置
HOST=0.0.0.0
PORT=8000
RELOAD=True

# 视频配置
VIDEO_PROXY_HOST=0.0.0.0
VIDEO_PROXY_PORT=8081
VIDEO_URL=http://0.0.0.0:8081/mjpeg
```

## 🚀 快速启动

### 一键启动（推荐）
```bash
python start_all.py
```

这将自动启动：
- 视频代理服务器（端口 8081）
- 后端 API 服务器（端口 8000）
- 前端开发服务器（端口 5173）
- 自动打开浏览器访问应用

### 手动分步启动

1. **启动视频代理服务器**：
```bash
python video_proxy_async.py --source http://192.168.4.1:81/stream
```

2. **启动后端服务器**：
```bash
python main.py
```

3. **启动前端服务器**：
```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

### 访问应用
- **前端界面**：http://localhost:5173
- **后端 API**：http://localhost:8000
- **视频代理**：http://localhost:8081

## 🔌 嵌入式设备设置

### ESP32-S3-LCD-EV-Board v1.5

1. 安装 PlatformIO IDE 或 CLI
2. 进入固件目录：
```bash
cd firmware-esp-lcd-ev
```
3. 编译并上传：
```bash
pio run --target upload
```

### ESP-CAM

1. 进入固件目录：
```bash
cd firmware-esp-cam
```
2. 编译并上传：
```bash
pio run --target upload
```

## 💡 使用说明

1. **设备连接**：通过 USB 将 ESP32 设备连接到上位机
2. **系统配置**：访问设置页面配置视频源和检测参数
3. **开始监控**：在仪表板上查看实时健康监测结果
4. **多设备支持**：添加更多 ESP32 设备实现多角度监控

## 🔍 系统组件详解

### 后端服务
- **监控注册器**：管理多个摄像头实例
- **视频处理器**：处理视频流和 YOLO 推理
- **健康分析器**：分析工作行为并生成洞察
- **生成服务**：使用 LLM 创建健康建议
- **电流处理器**：处理来自嵌入式设备的传感器数据

### 前端功能
- **实时仪表板**：实时健康监控显示
- **3D 可视化**：使用 Three.js 的交互式 3D 界面
- **多摄像头视图**：同时监控多个工位
- **健康分析**：历史数据可视化和趋势分析
- **设置面板**：设备和参数的配置管理

### 嵌入式功能
- **LVGL 界面**：LCD 显示屏上的触摸友好用户界面
- **USB 图传**：高性能视频传输
- **WebSocket 客户端**：与上位机的实时通信
- **低功耗设计**：针对连续运行优化

## 🛠️ 开发指南

### 架构原则
- **胖服务端策略**：前后端沟通的核心是 websocket 里的 insights。后端直接生成完整 insights message，前端不应该动态更新数据
- **不要 Overengineering**：保持代码实现简短简单，如果可能，减少代码的更改
- **多摄像头支持**：对多摄像头（多 monitor.py）的支持要格外留意
- **统一时间格式**：时间的数据类型统一采用 time.time() 转 int 的秒级时间戳，这样在嵌入式端也更好操作

### 项目结构
```
workhealthy/
├── backend/              # FastAPI 后端服务
├── frontend/             # Vue.js 前端应用
├── firmware-esp-lcd-ev/  # ESP32-S3-LCD-EV-Board 固件
├── firmware-esp-cam/     # ESP-CAM 固件
├── database/             # SQLite 数据库工具
├── start_all.py          # 一键启动脚本
├── video_proxy_async.py  # 异步视频代理服务器
└── requirements.txt      # Python 依赖
```

## 📊 健康监测功能

- **人员检测**：检测工位是否有人
- **活动监测**：分析运动模式和频率
- **姿态分析**：监控坐姿和位置
- **饮水跟踪**：检测饮水习惯并提醒喝水
- **工作时长**：跟踪连续工作时间防止久坐
- **休息提醒**：智能建议休息和活动

## 🐛 故障排除

### 视频流问题
- 检查视频代理服务器是否运行：http://localhost:8081/mjpeg
- 验证 ESP32 设备已连接并正在流传输
- 检查 USB 数据线和连接稳定性

### 后端问题
- 验证后端 API 是否响应：http://localhost:8000/status
- 检查 Python 依赖是否正确安装
- 查看控制台输出的错误信息

### 前端问题
- 确保 Node.js 和 npm 正确安装
- 检查所有前端依赖是否已安装
- 验证浏览器支持 WebSocket 连接

### 嵌入式设备问题
- 检查 PlatformIO 安装和板卡配置
- 验证 platformio.ini 中的正确板卡选择
- 监控串口输出以获取调试信息

## 📄 许可证

该项目采用 MIT 许可证。详情请参见 LICENSE 文件。

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

## 📞 支持

如需支持和问题咨询，请在 GitHub 上提交 issue。