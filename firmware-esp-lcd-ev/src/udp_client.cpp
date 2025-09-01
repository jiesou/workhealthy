#include "udp_client.h"
#include <Arduino.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <errno.h>
#include "esp_log.h"

#define CHUNK_LENGTH 1472
#define UDP_SERVER_IP "192.168.10.102"
#define UDP_SERVER_PORT 8099

static const char *TAG = "UDP_CLIENT";
static int udp_socket = -1;
static struct sockaddr_in udp_server_addr;
static uint8_t send_buffer[CHUNK_LENGTH];

static int send_with_retry(int sockfd, const void *buf, size_t len, int flags,
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
            vTaskDelay(pdMS_TO_TICKS(80)); // 短暂等待
            continue;
        }
        // 其他错误直接退出
        ESP_LOGE(TAG, "Send error: %d (errno=%d)", sent, errno);
        return -1;
    }
}

static esp_err_t setup_connection(void)
{
    if (udp_socket != -1)
    {
        close(udp_socket);
    }

    udp_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (udp_socket < 0)
    {
        ESP_LOGE(TAG, "Failed to create UDP socket");
        return ESP_FAIL;
    }

    // 设置服务器地址
    udp_server_addr.sin_family = AF_INET;
    udp_server_addr.sin_port = htons(UDP_SERVER_PORT);
    inet_pton(AF_INET, UDP_SERVER_IP, &udp_server_addr.sin_addr);

    // 设置为阻塞模式
    // int flags = fcntl(udp_socket, F_GETFL, 0);
    // fcntl(udp_socket, F_SETFL, flags & ~O_NONBLOCK);

    ESP_LOGI(TAG, "UDP Socket started, server: %s:%d", UDP_SERVER_IP, UDP_SERVER_PORT);
    return ESP_OK;
}

void udp_client_init(void)
{
    esp_err_t ret = setup_connection();
    if (ret != ESP_OK)
    {
        ESP_LOGE(TAG, "Failed to initialize UDP client");
    }
}

// 包头结构体
typedef struct
{
    uint32_t frame_index;
    uint16_t chunk_index;
    uint16_t chunk_total;
} __attribute__((packed)) udp_img_header_t;

esp_err_t udp_client_push_img(const uint8_t *data, size_t data_len)
{
    if (udp_socket < 0)
    {
        ESP_LOGE(TAG, "UDP socket not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (data == NULL || data_len == 0)
    {
        ESP_LOGE(TAG, "Invalid data or length");
        return ESP_ERR_INVALID_ARG;
    }

    static uint32_t frame_index = 0;
    // 计算单个分片能承载的长度
    size_t chunk_payload_len = CHUNK_LENGTH - sizeof(udp_img_header_t);
    // 计算总分片数，实现向上取整
    uint16_t chunk_total = (data_len + chunk_payload_len - 1) / chunk_payload_len;

    for (uint16_t chunk_index = 0; chunk_index < chunk_total; ++chunk_index)
    {
        size_t offset = chunk_index * chunk_payload_len;
        // 当前分片如果是最后一片，则直接为当前剩余数据长度 (data_len - offset)
        size_t this_len = (offset + chunk_payload_len > data_len) ? (data_len - offset) : chunk_payload_len;

        // 组包
        udp_img_header_t header = {
            .frame_index = frame_index,
            .chunk_index = chunk_index,
            .chunk_total = chunk_total};
        memcpy(send_buffer, &header, sizeof(header));
        memcpy(send_buffer + sizeof(header), data + offset, this_len);

        int ret = send_with_retry(
            udp_socket,
            send_buffer,
            this_len + sizeof(header),
            0,
            (struct sockaddr *)&udp_server_addr,
            sizeof(udp_server_addr));
        if (ret < 0)
        {
            ESP_LOGE(TAG, "Failed to send chunk %u", chunk_index);
            return ESP_FAIL;
        }
    }

    frame_index++;
    return ESP_OK;
}