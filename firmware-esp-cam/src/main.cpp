#include <Arduino.h>
#include "USB_STREAM.h"
#include "esp_heap_caps.h"

/* Define the camera frame callback function implementation */
static void onCameraFrameCallback(uvc_frame *frame, void *user_ptr)
{
  if (!frame || !frame->data)
  {
    return;
  }
  Serial.printf("uvc callback! frame_format = %d, seq = %" PRIu32 ", width = %" PRIu32 ", height = %" PRIu32 ", length = %u\n",
                frame->frame_format, frame->sequence, frame->width, frame->height, frame->data_bytes);
}

void setup()
{
  Serial.begin(115200);
  delay(2000); // 给系统更多启动时间

  Serial.println("Starting USB camera initialization...");

  // 使用更小的缓冲区，更适配高频配置
  const size_t buffer_size = 60 * 1024; // 60KB instead of 55KB

  // 使用DMA兼容内存，32字节对齐以适配缓存行
  uint8_t *_xferBufferA = (uint8_t *)heap_caps_aligned_alloc(32, buffer_size, MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
  assert(_xferBufferA != NULL);

  uint8_t *_xferBufferB = (uint8_t *)heap_caps_aligned_alloc(32, buffer_size, MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
  assert(_xferBufferB != NULL);

  uint8_t *_frameBuffer = (uint8_t *)heap_caps_aligned_alloc(32, buffer_size, MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
  assert(_frameBuffer != NULL);

  // Instantiate an object
  USB_STREAM *usb = new USB_STREAM();

  // Config with smaller resolution for stability
  usb->uvcConfiguration(320, 240, FRAME_INTERVAL_FPS_10, buffer_size, _xferBufferA, _xferBufferB, buffer_size, _frameBuffer);

  // Register the camera frame callback function
  usb->uvcCamRegisterCb(&onCameraFrameCallback, NULL);

  Serial.println("Starting USB stream...");
  usb->start();

  // Serial.println("Waiting for USB connection...");
  // usb->connectWait(3000); // 增加等待时间
  // delay(2000);

  // Serial.println("USB camera initialized successfully");

  /*Dont forget to free the allocated memory*/
  // free(_xferBufferA);
  // free(_xferBufferB);
  // free(_frameBuffer);
}

void loop()
{
  vTaskDelay(100);
}