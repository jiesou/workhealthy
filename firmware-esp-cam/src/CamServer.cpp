#include "CamServer.h"
#include <WiFiUdp.h>
#define CHUNK_LENGTH 1023

WiFiUDP udp;

void CamServer::init()
{
    server = new AsyncWebServer(80);
}

void CamServer::update()
{
}
// 性能统计变量
static unsigned long last_frame_time = 0;
static unsigned long frame_count = 0;
void CamServer::broadcastImg(uint8_t *img_buf, size_t img_len)
{
    // tks: https://github.com/0015/ThatProject/blob/master/ESP32CAM_Projects/ESP32_CAM_UDP/ESP32CAM_UDP_CLIENT/ESP32CAM_UDP_CLIENT.ino#L127-L145
    uint8_t buffer[CHUNK_LENGTH];
    size_t buffer_len = sizeof(buffer);
    size_t rest = img_len % buffer_len;
    
    for (uint8_t i = 0; i < img_len / buffer_len; ++i)
    {
        memcpy(buffer, img_buf + (i * buffer_len), buffer_len);
        udp.beginPacket(udpServerIP, udpServerPort);
        udp.write(buffer, CHUNK_LENGTH);
        udp.endPacket();
    }
    // 最后一小截不满 CHUNK_LENGTH 的包
    if (rest)
    {
        memcpy(buffer, img_buf + (img_len - rest), rest);
        udp.beginPacket(udpServerIP, udpServerPort);
        udp.write(buffer, rest);
        udp.endPacket();
    }
    
    unsigned long current_time = millis();
    frame_count++;
    // 输出当前帧信息
    Serial.printf("[CamServer] Frame #%lu: %zu bytes, interval: %lu ms\n",
        frame_count, img_len, current_time - last_frame_time);
    last_frame_time = current_time;
}

CamServer camServer;