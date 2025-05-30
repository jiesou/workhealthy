
#pragma once
#include "freertos/FreeRTOS.h"
#include "esp_err.h"

void udp_client_init(void);
esp_err_t udp_client_push_img(const uint8_t *data, size_t len);