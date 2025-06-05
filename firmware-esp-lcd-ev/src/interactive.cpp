#include "interactive.h"
#include <Adafruit_NeoPixel.h>
#include "lcd.h"

#define NUM_LEDS 1
#define LED_PIN 4

Adafruit_NeoPixel pixels(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

void interactive_init()
{
    pixels.begin();
    pixels.setBrightness(10);
    pixels.setPixelColor(0, pixels.Color(255, 0, 0)); // 初始颜色为红色
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

    if (doc["today_work_duration"].is<int>())
    {
        char duration_str[32];
        snprintf(duration_str, sizeof(duration_str), "%d", doc["today_work_duration"].as<int>());
        lcd_update_work_time(duration_str);
    }
    else
    {
        lcd_update_work_time("--");
    }
    pixels.show();
}
