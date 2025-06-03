#include "freertos/FreeRTOS.h"
#include "original/include/usb_stream.h"
#include "esp_log.h"
#include <WiFi.h>
#include <ArduinoJson.h>

#include "udp_client.h"
#include "wsclient.h"
#include "interactive.h"

#define LED_GPIO_NUM 4
#define FRAME_MEM_SIZE 60 * 1024 // 每个帧缓冲区大小 60KB

void camera_frame_cb(uvc_frame_t *frame, void *ptr)
{
  Serial.printf("[USB] Frame received: %dx%d, format: %d, size: %d bytes\n",
                frame->width, frame->height, frame->frame_format, frame->data_bytes);
  // 更新最新帧信息
  udp_client_push_img(static_cast<const uint8_t *>(frame->data), frame->data_bytes);
}

const char *ssid = "CMCC-SDyb";
const char *password = "2QiA74UZ";

void setup()
{
  Serial.begin(115200);
  Serial.setDebugOutput(true);

  // 配置 USB 摄像头
  uint8_t *xfer_buffer_a = (uint8_t *)malloc(FRAME_MEM_SIZE); // 60KB
  uint8_t *xfer_buffer_b = (uint8_t *)malloc(FRAME_MEM_SIZE); // 60KB
  uint8_t *frame_buffer = (uint8_t *)malloc(FRAME_MEM_SIZE);  // 60KB

  // 配置 UVC 参数
  uvc_config_t uvc_config = {
      .frame_width = 800,
      .frame_height = 480,
      .frame_interval = FRAME_INTERVAL_FPS_20,
      .xfer_buffer_size = FRAME_MEM_SIZE, // 60KB
      .xfer_buffer_a = xfer_buffer_a,
      .xfer_buffer_b = xfer_buffer_b,
      .frame_buffer_size = FRAME_MEM_SIZE, // 60KB
      .frame_buffer = frame_buffer,
      .frame_cb = &camera_frame_cb, // 核心回调函数
      .frame_cb_arg = NULL,
  };

  // 配置 UVC 流
  ESP_ERROR_CHECK(uvc_streaming_config(&uvc_config));

  // 启动 USB 流处理
  ESP_ERROR_CHECK(usb_streaming_start());

  Serial.println("USB device connected!");

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(50);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  Serial.print("Camera Ready! IP:");
  Serial.println(WiFi.localIP());

  udp_client_init();
  wsclient_init();
  interactive_init();
  pinMode(LED_GPIO_NUM, OUTPUT);
  wsclient_on_message([](const String &message)
                      {
    Serial.printf("[wsclient] Received message: %s\n", message.c_str());
    // 这里可以处理接收到的消息
    JsonDocument doc;
    deserializeJson(doc, message); 
    interactive_update(doc);
  });

  // 核心分配策略：
  // Core 0: 系统任务 + UDP图传
  // Core 1: wsclient 任务

  // wsclient 任务 - 固定在 Core 1
  static TaskHandle_t wsTaskHandle = NULL;
  xTaskCreatePinnedToCore(
      [](void *)
      {
        for (;;)
        {
          wsclient_update();
          vTaskDelay(500 / portTICK_PERIOD_MS); // 500ms 刷新一次 wsclient
        }
      },
      "wsclient_task",
      4096,
      NULL,
      1,
      &wsTaskHandle,
      1);

  esp_log_level_set("*", ESP_LOG_INFO);
}

void loop()
{
  // wsclient_update();
  // camServer.update(); // 必须每次都调用
  // vTaskDelay(1000 / portTICK_PERIOD_MS); // 每秒更新一次
}