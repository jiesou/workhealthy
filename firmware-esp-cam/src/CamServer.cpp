#include "CamServer.h"
#include <WiFiUdp.h>
#define CHUNK_LENGTH 1023

static int udp_socket = -1;
static struct sockaddr_in server_addr;

void CamServer::init()
{
    setupConnection();
}

void CamServer::update()
{
}

int sendWithRetry(int sockfd, const void *buf, size_t len, int flags,
                             const struct sockaddr *dest_addr, socklen_t addrlen)
{
    while (1)
    {
        int sent = sendto(sockfd, buf, len, flags, dest_addr, addrlen);
        if (sent == (int)len)
        {
            return sent; // 成功发送
        }
        if (sent == -1 && (errno == ENOMEM))
        {
            delay(80); // 短暂等待（根据实际调整）
            continue;
        }
        // 其他错误直接退出
        Serial.printf("Send error: %d (errno=%d)\n", sent, errno);
        return -1;
    }
}

void CamServer::setupConnection()
{
    if (udp_socket != -1)
    {
        close(udp_socket);
    }
    udp_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (udp_socket < 0)
    {
        Serial.println("Failed to create UDP socket.");
        return;
    }
    server_addr.sin_addr.s_addr = udpServerIP; // 服务器 IP 地址
    server_addr.sin_family = AF_INET; // IPv4
    server_addr.sin_port = htons(udpServerPort); // 服务器端口号

    int flags = fcntl(udp_socket, F_GETFL, 0);
    fcntl(udp_socket, F_SETFL, flags & ~O_NONBLOCK); // 清除非阻塞标志
    Serial.println("UDP Socket started.");
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
        sendWithRetry(udp_socket, buffer, buffer_len, 0,
                          (struct sockaddr *)&server_addr, sizeof(server_addr));
    }
    // 最后一小截不满 CHUNK_LENGTH 的包
    if (rest)
    {
        memcpy(buffer, img_buf + (img_len - rest), rest);
        sendWithRetry(udp_socket, buffer, rest, 0,
                          (struct sockaddr *)&server_addr, sizeof(server_addr));
    }

    unsigned long current_time = millis();
    frame_count++;
    // 输出当前帧信息
    Serial.printf("[CamServer] Frame #%lu: %zu bytes, interval: %lu ms\n",
        frame_count, img_len, current_time - start_frame_time);
    start_frame_time = current_time;
    delay(10); // 延时 10ms，避免过快发送
}

CamServer camServer;