# WorkHealthy - Office Health Monitoring System

[简体中文](README.zh.md)

A comprehensive office worker health monitoring system using computer vision (YOLO) and LLM to monitor workplace health status. It's like a real-world "screen time" tracker that provides real-time health feedback and recommendations based on workers' posture, activity patterns, and hydration habits.

## Features

- **Real-time Health Monitoring**: Tracks posture, activity frequency, and hydration habits, with companion smart sockets for power consumption tracking (smart socket is from an existing project, not yet fully open-sourced)
- **Multi-camera Support**: One host computer can connect to multiple embedded devices simultaneously
- **AI-powered Analysis**: Uses YOLO computer vision models for person detection and activity analysis
- **LLM Integration**: Provides intelligent health recommendations and insights
- **Real-time Feedback**: WebSocket-based real-time communication and updates
- **Embedded Interfaces**: LVGL-based user interfaces on ESP32 devices
- **USB Streaming**: Uses usb_stream for USB camera support with UDP self-assembled packets for high-performance video transmission

## System Architecture

The system consists of two main components:

### Host Computer (上位机)
- **Frontend**: Vue.js application with partial use of Three.js and TresJS for 3D visualization
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

## Hardware Requirements

### Host Computer
- Docker

### Embedded Devices
- **ESP32-S3-LCD-EV-Board v1.5** OR **ESP-CAM**
- USB cable for connection and power
- Camera module (integrated in both boards)

## Installation

Use devcontainer

Frontend dependencies can be installed with `yarn`

Backend requires editing `.env.example`

Edit [`api/monitor.py`](https://github.com/jiesou/workhealthy/blob/d3066bf7cae3a1f2b7ac972445f81eb29522e923/backend/api/monitor.py#L22-L23) to register required embedded cameras. The `current_sensor_url` parameter is for connecting the non-open-source smart socket and can be left blank.

Then run `python main.py` to start

### Access the Application
- **Frontend Interface**: http://localhost:5173
- **Backend API**: http://localhost:8000

## Embedded Firmware Flashing

1. Switch to the corresponding directory's `.code-workspace` (required, otherwise PlatformIO won't recognize the project)

2. Edit host computer related information:

- Video streaming: [UDP_SERVER_IP](https://github.com/jiesou/workhealthy/blob/d3066bf7cae3a1f2b7ac972445f81eb29522e923/firmware-esp-lcd-ev/src/udp_client.cpp#L9C9-L9C22)
- WebSocket: [WS_SERVER_HOST](https://github.com/jiesou/workhealthy/blob/d3066bf7cae3a1f2b7ac972445f81eb29522e923/firmware-esp-lcd-ev/src/wsclient.cpp#L4)
- WiFi (MCU as STA, requires external AP): [ssid/password](https://github.com/jiesou/workhealthy/blob/d3066bf7cae3a1f2b7ac972445f81eb29522e923/firmware-esp-lcd-ev/src/main.cpp#L24)

3. Build, then run `pio run --target upload`

### Architecture Principles
- **Fat Server Strategy**: Frontend-backend communication core is [`insights`](https://github.com/jiesou/workhealthy/blob/d3066bf7cae3a1f2b7ac972445f81eb29522e923/backend/monitor.py#L52-L102) in websocket. Backend generates complete insights messages directly, frontend should not dynamically update data
- **No Over-engineering**: Keep code implementation short and simple, reduce code changes if possible
- **Multi-camera Support**: Pay special attention to supporting multiple cameras (multiple monitor.py instances)
- **Unified Time Format**: For better operation on embedded devices, time data type uniformly uses time.time() converted to int second-level timestamps, not datetime 