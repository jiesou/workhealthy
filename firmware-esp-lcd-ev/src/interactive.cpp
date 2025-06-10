#include "interactive.h"
#include <Adafruit_NeoPixel.h>
#include "lcd.h"
#include "wsclient.h"

#define NUM_LEDS 1
#define LED_PIN 4

Adafruit_NeoPixel pixels(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

void interactive_init()
{
    pixels.begin();
    pixels.setBrightness(50);
    pixels.setPixelColor(0, pixels.Color(255, 100, 50)); // 初始颜色为黄色
    pixels.show();
}

void interactive_update(JsonDocument &doc)
{
    if (doc["person_detected"].is<bool>())
    {
        Serial.printf("[wsclient] Person detected: %s\n", doc["person_detected"] ? "true" : "false");
        if (doc["person_detected"] == true)
        {
            pixels.setBrightness(100);
            pixels.setPixelColor(0, pixels.Color(255, 255, millis() % 256)); // 颜色变化
            lcd_update_person_detected(true);
        }
        else
        {
            pixels.setPixelColor(0, pixels.Color(0, 0, 0)); // 关闭 LED
            lcd_update_person_detected(false);
        }
    }
    else
    {
        pixels.setPixelColor(0, pixels.Color(255, 0, 0));
    }

    if (doc["generator_summary_health_message"].is<const char *>())
    {
        Serial.printf("[wsclient] Generator summary: %s\n", doc["generator_summary_health_message"].as<const char *>());
        lcd_update_ai_summary(doc["generator_summary_health_message"].as<const char *>());
    }

    if (doc["today_work_duration_message"].is<const char *>())
    {
        lcd_update_work_time(doc["today_work_duration_message"].as<const char *>());
    }
    else
    {
        lcd_update_work_time("--");
    }
    if (doc["water_intake_message"].is<const char *>())
    {
        lcd_update_cup_detect(doc["water_intake_message"].as<const char *>());
    }
    else
    {
        lcd_update_cup_detect("未检测到水杯");
    }
    pixels.show();
}

void interactive_push_ai_summary_refresh()
{
    wsclient_send_message("{ "
                          "\"action\": \"refresh_generator_summary_health\" "
                          "}");
}
