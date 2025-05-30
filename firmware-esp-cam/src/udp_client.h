
#pragma once
#include <stdint.h>
#include <stddef.h>
#include "esp_err.h"
#include "esp_event.h"

void udp_client_init(void);
esp_err_t udp_client_push_img(const uint8_t *data, size_t len);