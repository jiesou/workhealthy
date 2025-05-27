#include "esp_camera.h"
#include <WiFi.h>

#include "CamServer.h"

//
// WARNING!!! PSRAM IC required for UXGA resolution and high JPEG quality
//            Ensure ESP32 Wrover Module or other board with PSRAM is selected
//            Partial images will be transmitted if image exceeds buffer size
//
//            You must select partition scheme from the board menu that has at least 3MB APP space.
//            Face Recognition is DISABLED for ESP32 and ESP32-S2, because it takes up from 15
//            seconds to process single frame. Face Detection is ENABLED if PSRAM is enabled as well

#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

const char *ssid = "CMCC-SDyb";
const char *password = "2QiA74UZ";

void setup()
{
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_QVGA;   // 分辨率
  config.pixel_format = PIXFORMAT_JPEG; // 直接传给后端 MJPEG
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 33;

  // 确认 PSRAM 可用
  if (psramFound())
  {
    Serial.println("PSRAM ok!");
    config.jpeg_quality = 20;
    config.fb_count = 3;
    config.grab_mode = CAMERA_GRAB_LATEST;
  }

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK)
  {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  // 适用于 OV2640
  s->set_vflip(s, 0);      // 不反转垂直方向
  s->set_brightness(s, 1); // 亮一点
  s->set_saturation(s, 0); // 减少饱和度
  s->set_awb_gain(s, 1);   // 启用自动白平衡增益
  s->set_exposure_ctrl(s, 1); // 启用自动曝光

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);
  WiFi.setTxPower(WIFI_POWER_19_5dBm); // 设置 WiFi 发射功率最大

  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(50);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  // startCameraServer();

  Serial.print("Camera Ready! IP:");
  Serial.println(WiFi.localIP());

  camServer.init();
}

camera_fb_t *fb = NULL;
esp_err_t res = ESP_OK;

unsigned long lastCaptureTime = 0;

void loop()
{
  // camServer.update(); // 必须每次都调用

  unsigned long now = millis();
  if (now - lastCaptureTime > 100)
  { // 控制 10 帧
    fb = esp_camera_fb_get();
    if (fb)
    {
      camServer.broadcastImg(fb->buf, fb->len);
      esp_camera_fb_return(fb);
    }
    lastCaptureTime = now;
  }
}