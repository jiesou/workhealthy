#pragma once
#include <HTTPClient.h>
#include <ArduinoJson.h>

class Httper
{
private:
public:
    void init();
    void update();
    HTTPClient httpClient;
};

extern Httper httper;