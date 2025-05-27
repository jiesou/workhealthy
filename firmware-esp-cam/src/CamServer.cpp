#include "CamServer.h"
#include "Httper.h"
#include <AsyncUDP.h>

AsyncUDP udp;

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

    const size_t max_packet_size = 1024;
    uint16_t total_packets = img_len / max_packet_size + (img_len % max_packet_size != 0);
    static uint16_t frame_id = 0;

    for (uint16_t i = 0; i < total_packets; i++)
    {
        size_t start = i * max_packet_size;
        size_t end = min(start + max_packet_size, img_len);
        size_t chunk_size = end - start;

        // 包头：2字节帧号 + 2字节包号 + 2字节总包数
        uint8_t buf[6 + max_packet_size];
        buf[0] = frame_id >> 8;
        buf[1] = frame_id & 0xFF;
        buf[2] = i >> 8;
        buf[3] = i & 0xFF;
        buf[4] = total_packets >> 8;
        buf[5] = total_packets & 0xFF;
        memcpy(buf + 6, img_buf + start, chunk_size);
        
        udp.writeTo(buf, 6 + chunk_size, IPAddress(192, 168, 10, 101), 8099);
        delay(1); // 控制速率
    }

    frame_id++;

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
    Serial.printf("[CamServer] Frame #%lu: %zu bytes, interval: %lu ms\n",
                  frame_count, img_len, frame_interval);
}

void CamServer::setupWebServer()
{
    Serial.println("AsyncWebServer started.");
}

CamServer camServer;