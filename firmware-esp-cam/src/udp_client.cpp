#include "udp_client.h"
#include <string.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define CHUNK_LENGTH 1472
#define UDP_SERVER_IP "192.168.10.101" // 修改为你的服务器IP
#define UDP_SERVER_PORT 8099           // 修改为你的服务器端口

static const char *TAG = "UDP_CLIENT";
static int udp_socket = -1;
static struct sockaddr_in server_addr;
static unsigned long frame_count = 0;
static uint8_t send_buffer[CHUNK_LENGTH]; // 将缓冲区改为静态变量

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
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(UDP_SERVER_PORT);
    inet_pton(AF_INET, UDP_SERVER_IP, &server_addr.sin_addr);

    // 设置为阻塞模式
    int flags = fcntl(udp_socket, F_GETFL, 0);
    fcntl(udp_socket, F_SETFL, flags & ~O_NONBLOCK);

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

esp_err_t udp_client_push_img(const uint8_t *data, size_t len)
{
    if (udp_socket < 0)
    {
        ESP_LOGE(TAG, "UDP socket not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (data == NULL || len == 0)
    {
        ESP_LOGE(TAG, "Invalid data or length");
        return ESP_ERR_INVALID_ARG;
    }

    static uint32_t start_frame_time = 0;
    size_t buffer_len = sizeof(send_buffer);
    size_t rest = len % buffer_len;

    // 发送完整的块
    for (size_t i = 0; i < len / buffer_len; ++i)
    {
        memcpy(send_buffer, data + (i * buffer_len), buffer_len);
        int ret = send_with_retry(udp_socket, send_buffer, buffer_len, 0,
                                  (struct sockaddr *)&server_addr, sizeof(server_addr));
        if (ret < 0)
        {
            ESP_LOGE(TAG, "Failed to send chunk %zu", i);
            return ESP_FAIL;
        }
    }

    // 发送剩余的不完整块
    if (rest)
    {
        memcpy(send_buffer, data + (len - rest), rest);
        int ret = send_with_retry(udp_socket, send_buffer, rest, 0,
                                  (struct sockaddr *)&server_addr, sizeof(server_addr));
        if (ret < 0)
        {
            ESP_LOGE(TAG, "Failed to send last chunk");
            return ESP_FAIL;
        }
    }

    // 统计信息
    uint32_t current_time = xTaskGetTickCount() * portTICK_PERIOD_MS;
    frame_count++;
    ESP_LOGI(TAG, "Frame #%lu: %zu bytes, interval: %lu ms",
             frame_count, len, current_time - start_frame_time);
    start_frame_time = current_time;

    // 延时避免过快发送
    vTaskDelay(pdMS_TO_TICKS(10));

    return ESP_OK;
}