#include "CamServer.h"
#include "Httper.h"
#include <AsyncWebSocket.h>

AsyncWebSocket ws("/ws");

void CamServer::init()
{
    server = new AsyncWebServer(80);
    setupWebServer();
}

void CamServer::update()
{
}
// 性能统计变量
static unsigned long last_frame_time = 0;
static unsigned long frame_count = 0;
static unsigned long total_bytes_sent = 0;
static unsigned long stats_start_time = 0;

void CamServer::broadcastImg(uint8_t *img_buf, size_t img_len)
{
    unsigned long current_time = millis();

    if (!ws.count() > 0)
        return;
    // 清理断开的客户端
    ws.cleanupClients();

    // 检查所有客户端的队列状态，先检查再发送
    if (!ws.availableForWriteAll())
    {
        Serial.println("[CamServer] Some WebSocket queues are full, skipping frame.");
        ws.closeAll(1000, "Queue full");
        return;
    }

    ws.binaryAll(img_buf, img_len);

    // 统计帧率和传输量
    frame_count++;
    total_bytes_sent += img_len;

    // 计算帧间隔
    unsigned long frame_interval = 0;
    if (last_frame_time > 0)
    {
        frame_interval = current_time - last_frame_time;
    }
    last_frame_time = current_time;

    // 输出当前帧信息
    Serial.printf("[CamServer] Frame #%lu: %zu bytes, interval: %lu ms, clients: %d\n",
                  frame_count, img_len, frame_interval, ws.count());
}

void CamServer::setupWebServer()
{
    ws.onEvent([this](AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len)
               {
        if (type == WS_EVT_CONNECT) {
            Serial.printf("[CamServer] WebSocket client #%u connected\n", client->id());
        } else if (type == WS_EVT_DISCONNECT) {
            Serial.printf("[CamServer] WebSocket client #%u disconnected\n", client->id());
        } });
    server->addHandler(&ws);

    server->on("/", HTTP_GET, [](AsyncWebServerRequest *request)
               { request->send(200, "text/html",
                               "<html><body>"
                               "<h2>ESP32-CAM Stream</h2>"
                               "<img id='wsStream' style='width:480px'>"
                               "<script>"
                               "const ws = new WebSocket('ws://' + location.host + '/ws');"
                               "ws.binaryType = 'arraybuffer';"
                               "ws.onmessage = function(event) {"
                               "  const img = document.getElementById('wsStream');"
                               "  const blob = new Blob([event.data], {type: 'image/jpeg'});"
                               "  img.src = URL.createObjectURL(blob);"
                               "};"
                               "</script>"
                               "</body></html>"); });

    server->begin(); // 启动服务器
    Serial.println("AsyncWebServer started.");
}

CamServer camServer;