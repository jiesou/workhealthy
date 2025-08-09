# WorkHealthy - Office Health Monitoring System

A comprehensive office worker health monitoring system using computer vision (YOLO) and LLM to monitor workplace health status. It's like a real-world "screen time" tracker that provides real-time health feedback and recommendations based on workers' posture, activity patterns, and hydration habits.

## 🎯 Features

- **Real-time Health Monitoring**: Tracks posture, activity frequency, and hydration habits
- **Multi-camera Support**: One host computer can connect to multiple embedded devices simultaneously
- **AI-powered Analysis**: Uses YOLO computer vision models for person detection and activity analysis
- **LLM Integration**: Provides intelligent health recommendations and insights
- **Real-time Feedback**: WebSocket-based real-time communication and updates
- **Embedded Interfaces**: LVGL-based user interfaces on ESP32 devices
- **USB Streaming**: High-performance video transmission using usb_stream library

## 🏗️ System Architecture

The system consists of two main components:

### Host Computer (上位机)
- **Frontend**: Vue.js application with 3D visualization using Three.js and TresJS
- **Backend**: FastAPI with SQLite database
- **Video Processing**: Real-time YOLO model inference (YOLOv8, YOLO11)
- **Health Analysis**: Intelligent monitoring and recommendation engine
- **Multi-stream Support**: Handles multiple camera feeds simultaneously

### Embedded Devices (下位机)
Two firmware versions supporting different ESP32 boards:

1. **ESP32-S3-LCD-EV-Board v1.5**: Advanced version with LCD display and LVGL interface
2. **ESP-CAM**: Compact camera-only version

Both firmwares feature:
- PlatformIO Arduino/FreeRTOS development
- USB streaming using usb_stream library
- WebSocket communication with host computer
- Real-time video transmission

## 🔧 Hardware Requirements

### Host Computer
- Python 3.8+
- Node.js 14+
- USB ports for connecting embedded devices
- GPU recommended for faster YOLO inference

### Embedded Devices
- **ESP32-S3-LCD-EV-Board v1.5** OR **ESP-CAM**
- USB cable for connection and power
- Camera module (integrated in both boards)

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/jiesou/workhealthy.git
cd workhealthy
```

### 2. Setup Python Environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Setup Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 4. Configure Environment
```bash
cp env.example .env
```

Edit `.env` file according to your setup:
```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=True

# Video Configuration
VIDEO_PROXY_HOST=0.0.0.0
VIDEO_PROXY_PORT=8081
VIDEO_URL=http://0.0.0.0:8081/mjpeg
```

## 🚀 Quick Start

### One-click Startup (Recommended)
```bash
python start_all.py
```

This will automatically start:
- Video proxy server (Port 8081)
- Backend API server (Port 8000)
- Frontend development server (Port 5173)
- Web browser pointing to the application

### Manual Startup

1. **Start Video Proxy Server**:
```bash
python video_proxy_async.py --source http://192.168.4.1:81/stream
```

2. **Start Backend Server**:
```bash
python main.py
```

3. **Start Frontend Server**:
```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

### Access the Application
- **Frontend Interface**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Video Proxy**: http://localhost:8081

## 🔌 Embedded Device Setup

### ESP32-S3-LCD-EV-Board v1.5

1. Install PlatformIO IDE or CLI
2. Navigate to firmware directory:
```bash
cd firmware-esp-lcd-ev
```
3. Build and upload:
```bash
pio run --target upload
```

### ESP-CAM

1. Navigate to firmware directory:
```bash
cd firmware-esp-cam
```
2. Build and upload:
```bash
pio run --target upload
```

## 💡 Usage

1. **Setup**: Connect your ESP32 device(s) to the host computer via USB
2. **Configuration**: Access the settings page to configure video sources and detection parameters
3. **Monitoring**: View real-time health monitoring results on the dashboard
4. **Multi-device**: Add additional ESP32 devices for multi-angle monitoring

## 🔍 System Components

### Backend Services
- **Monitor Registry**: Manages multiple camera instances
- **Video Processor**: Handles video stream processing and YOLO inference
- **Health Analyzer**: Analyzes worker behavior and generates insights
- **Generator Service**: Creates health recommendations using LLM
- **Current Processor**: Handles sensor data from embedded devices

### Frontend Features
- **Real-time Dashboard**: Live health monitoring display
- **3D Visualization**: Interactive 3D interface using Three.js
- **Multi-camera View**: Simultaneous monitoring of multiple workstations
- **Health Analytics**: Historical data visualization and trends
- **Settings Panel**: Configuration management for devices and parameters

### Embedded Features
- **LVGL Interface**: Touch-friendly user interface on LCD displays
- **USB Streaming**: High-performance video transmission
- **WebSocket Client**: Real-time communication with host computer
- **Low Power Design**: Optimized for continuous operation

## 🛠️ Development

### Architecture Principles
- **Fat Server Strategy**: Backend generates complete insights messages; frontend displays without dynamic data manipulation
- **No Over-engineering**: Keep implementations simple and concise
- **Multi-camera Awareness**: Special attention to supporting multiple monitor.py instances
- **Unified Time Format**: Use Unix timestamps (time.time() converted to int) for embedded compatibility

### Project Structure
```
workhealthy/
├── backend/              # FastAPI backend services
├── frontend/             # Vue.js frontend application
├── firmware-esp-lcd-ev/  # ESP32-S3-LCD-EV-Board firmware
├── firmware-esp-cam/     # ESP-CAM firmware
├── database/             # SQLite database utilities
├── start_all.py          # One-click startup script
├── video_proxy_async.py  # Async video proxy server
└── requirements.txt      # Python dependencies
```

## 📊 Health Monitoring Features

- **Person Detection**: Detects presence at workstation
- **Activity Monitoring**: Analyzes movement patterns and frequency
- **Posture Analysis**: Monitors sitting posture and positioning
- **Hydration Tracking**: Detects drinking habits and reminds for water breaks
- **Work Duration**: Tracks continuous work periods to prevent prolonged sitting
- **Break Reminders**: Intelligent suggestions for rest and movement

## 🐛 Troubleshooting

### Video Stream Issues
- Check if video proxy server is running: http://localhost:8081/mjpeg
- Verify ESP32 device is connected and streaming
- Check USB cable and connection stability

### Backend Issues
- Verify backend API is responding: http://localhost:8000/status
- Check Python dependencies are installed correctly
- Review console output for error messages

### Frontend Issues
- Ensure Node.js and npm are installed correctly
- Check if all frontend dependencies are installed
- Verify browser supports WebSocket connections

### Embedded Device Issues
- Check PlatformIO installation and board configuration
- Verify correct board selection in platformio.ini
- Monitor serial output for debugging information

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For support and questions, please open an issue on GitHub. 