#pragma once
#include "freertos/FreeRTOS.h"
#include <esp_display_panel.hpp>
#include <lvgl.h>
#include "lvgl_v8_port.h"

using namespace esp_panel::drivers;
using namespace esp_panel::board;

void _createUI();

void lcd_init();
