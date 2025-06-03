#include "Httper.h"

void Httper::init()
{
    // Initialize HTTP client
    httper.httpClient.setReuse(true); // 复用TCP连接
}

void Httper::update()
{
    httpClient.begin("http://example.com");
    // Update HTTP client state
    int responseCode = httpClient.GET();
    if (responseCode < 0)
    {
        Serial.print("[Httper] Error on HTTP request:");
        Serial.println(httpClient.errorToString(responseCode).c_str());
    }
    String responseBody = httpClient.getString();

    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, responseBody);
    Serial.println("[Httper] Response: " + responseBody);
    if (error)
    {
        Serial.print("[Httper] deserializeJson() failed: ");
        Serial.println(error.c_str());
    }
    if (doc.containsKey("key"))
    {
        String value = doc["key"].as<String>();
        Serial.println("[Httper] Key value: " + value);
    }
}

Httper httper;