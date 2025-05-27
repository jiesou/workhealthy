#include "CamServer.h"
#include <WiFiUdp.h>
#define CHUNK_LENGTH 1472

static struct netconn *udp_conn = NULL;
static struct sockaddr_in server_addr;

void CamServer::init()
{
    setupConnection();
}

void CamServer::update()
{
}

void CamServer::sendUdpWithNetconn(struct netconn *conn, const void *data, size_t len)
{
    struct netbuf *buf = netbuf_new();
    if (!buf) {
        Serial.println("Failed to allocate netbuf.");
        return;
    }
    void *buf_data = netbuf_alloc(buf, len);
    if (!buf_data) {
        Serial.println("Failed to allocate netbuf data.");
        netbuf_delete(buf);
        return;
    }
    memcpy(buf_data, data, len);
    netconn_send(conn, buf);
    netbuf_delete(buf);
}

void CamServer::setupConnection()
{
    if (udp_conn)
    {
        netconn_delete(udp_conn);
        udp_conn = NULL;
    }

    udp_conn = netconn_new(NETCONN_UDP);
    netconn_set_nonblocking(udp_conn, 0);
    netconn_bind(udp_conn, &udpServerIP, udpServerPort);
    if (!udp_conn)
    {
        Serial.println("Failed to create UDP netconn.");
        return;
    }

    Serial.println("UDP Netconn started.");
}

// 性能统计变量
static unsigned long frame_count = 0;
void CamServer::broadcastImg(uint8_t *img_buf, size_t img_len)
{
    static unsigned long start_frame_time = millis();
    uint8_t buffer[CHUNK_LENGTH];
    size_t buffer_len = sizeof(buffer);
    size_t rest = img_len % buffer_len;
    
    for (uint8_t i = 0; i < img_len / buffer_len; ++i)
    {
        memcpy(buffer, img_buf + (i * buffer_len), buffer_len);
        sendUdpWithNetconn(udp_conn, buffer, buffer_len);
    }
    // 最后一小截不满 CHUNK_LENGTH 的包
    if (rest)
    {
        memcpy(buffer, img_buf + (img_len - rest), rest);
        sendUdpWithNetconn(udp_conn, buffer, rest);
    }

    unsigned long current_time = millis();
    frame_count++;
    // 输出当前帧信息
    Serial.printf("[CamServer] Frame #%lu: %zu bytes, interval: %lu ms\n",
        frame_count, img_len, current_time - start_frame_time);
}

CamServer camServer;