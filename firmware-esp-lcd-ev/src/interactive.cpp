#include "interactive.h"
#include <Adafruit_NeoPixel.h>
#include "lcd.h"

#define NUM_LEDS 1
#define LED_PIN 4

Adafruit_NeoPixel pixels(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

void interactive_init()
{
    pixels.begin();
    pixels.setBrightness(50);
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
        }
        else
        {
            pixels.setPixelColor(0, pixels.Color(0, 0, 0)); // 关闭 LED
        }
    }
    else
    {
        pixels.setPixelColor(0, pixels.Color(255, 0, 0));
    }

    if (doc["work_time"].is<int>())
    {
        lcd_update_work_time(doc["work_time"].as<String>().c_str());
    }
    else
    {
        lcd_update_work_time("未知");
    }
    pixels.show();
}
