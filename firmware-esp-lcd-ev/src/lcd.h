#pragma once
#include "esp_log.h"
#include <esp_display_panel.hpp>
#include <lvgl.h>
#include "lvgl_v8_port.h"

static const char *TAG = "LCDModule";

using namespace esp_panel::drivers;
using namespace esp_panel::board;

void lcd_init();

void lcd_update_connect_status(const bool connected);
void lcd_update_person_detected(const bool person_detected);
void lcd_update_cup_detect(const bool cup_detected);
void lcd_update_work_time(const char *text);
