# 工位健康检测系统

这是一个使用计算机视觉和人工智能技术来监测工位健康状况的系统。系统通过摄像头采集视频，分析工人的工作姿态、活动频率和饮水习惯，提供实时健康状态反馈和建议。

## 系统架构

系统由三个主要部分组成：

1. **前端** - 基于Vue.js的用户界面，提供实时监控视图和数据可视化
2. **后端** - 基于FastAPI的Python后端服务，处理视频分析和健康监测
3. **视频代理** - 独立的视频流处理服务，负责视频采集和分发

### 视频代理服务器

视频代理服务器是一个独立的组件，用于：

- 从摄像头或网络视频流获取视频帧
- 提供MJPEG流和单帧API
- 支持多客户端连接
- 通过Web界面管理视频源
- 完全分离视频采集和YOLO处理，避免资源竞争

这种架构设计能够有效解决视频处理和显示之间的资源竞争问题。

## 安装

### 环境要求

- Python 3.8+
- Node.js 14+
- 摄像头（本地USB摄像头或网络摄像头）

### 依赖安装

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/workhealthy.git
cd workhealthy
```

2. 创建Python虚拟环境并安装依赖：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
pip install -r requirements.txt
```

3. 安装前端依赖：

```bash
cd frontend
npm install
cd ..
```

## 配置

1. 复制环境变量示例文件：

```bash
cp env.example .env
```

2. 根据需要修改`.env`文件中的配置：

```
# 服务器配置
HOST=0.0.0.0
PORT=8000
RELOAD=True

# 视频配置
VIDEO_PROXY_HOST=0.0.0.0
VIDEO_PROXY_PORT=8081
VIDEO_URL=http://0.0.0.0:8081/mjpeg
```

## 运行

### 一键启动（推荐）

使用一键启动脚本同时启动视频代理、后端和前端服务：

```bash
python start_all.py
```

### 分别启动

1. 启动视频代理服务器：

```bash
python video_proxy.py
```

2. 启动后端服务：

```bash
python main.py
```

3. 启动前端服务：

```bash
cd frontend
npm run dev
```

## 使用说明

1. 访问前端界面：http://0.0.0.0:5173
2. 在"设置"页面配置视频源和检测参数
3. 在"实时监控"页面查看健康监测结果
4. 视频代理服务器入口页面：http://0.0.0.0:8081

## 系统功能

- 人体检测：检测工位是否有人
- 活动监测：分析工人活动频率
- 水杯检测：提醒适时饮水
- 工作时长统计：防止久坐不动

## 故障排除

- **视频流不显示**：检查视频代理服务器是否正常运行，访问 http://0.0.0.0:8081/mjpeg 确认
- **分析结果不更新**：检查后端API是否正常，访问 http://0.0.0.0:8000/status
- **前端加载失败**：检查Node.js环境和依赖是否正确安装

## 许可证

该项目采用MIT许可证 