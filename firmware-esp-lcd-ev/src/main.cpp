#include "freertos/FreeRTOS.h"
#include "original/include/usb_stream.h"
#include "esp_log.h"
#include <WiFi.h>

#include "udp_client.h"

void camera_frame_cb(uvc_frame_t *frame, void *ptr)
{
  Serial.printf("Updated frame: %dx%d, size: %zu bytes, sequence: %u\n",
                frame->width, frame->height, frame->data_bytes, frame->sequence);
  // if (frame->frame_format == UVC_FRAME_FORMAT_MJPEG)
  // {
  udp_client_push_img(static_cast<uint8_t *>(frame->data), frame->data_bytes);
  // }
}

const char *ssid = "CMCC-SDyb";
const char *password = "2QiA74UZ";

void setup()
{
  Serial.begin(115200);
  Serial.setDebugOutput(true);

  // 配置 USB 摄像头
  uint8_t *xfer_buffer_a = (uint8_t *)malloc(60 * 1024); // 60KB
  uint8_t *xfer_buffer_b = (uint8_t *)malloc(60 * 1024); // 60KB
  uint8_t *frame_buffer = (uint8_t *)malloc(60 * 1024);  // 60KB

  uint16_t uvc_frame_w = 800;
  uint16_t uvc_frame_h = 480;

  // 配置 UVC 参数
  uvc_config_t uvc_config = {
      .frame_width = uvc_frame_w,
      .frame_height = uvc_frame_h,
      .frame_interval = FRAME_INTERVAL_FPS_30,
      .xfer_buffer_size = 60 * 1024, // 60KB
      .xfer_buffer_a = xfer_buffer_a,
      .xfer_buffer_b = xfer_buffer_b,
      .frame_buffer_size = 60 * 1024, // 60KB
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
  esp_log_level_set("*", ESP_LOG_INFO);
}

void loop()
{
  // camServer.update(); // 必须每次都调用
  vTaskDelay(1000 / portTICK_PERIOD_MS); // 每秒更新一次
}