#pragma once
#include <ArduinoJson.h>

void interactive_init();
void interactive_update(JsonDocument &doc);
void interactive_push_ai_summary_refresh();
