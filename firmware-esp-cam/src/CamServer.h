#pragma once
#include <Arduino.h>
#include <ESPAsyncWebServer.h>
#include <cstdint>
#include <cstddef>

class CamServer
{
private:
    AsyncWebServer *server;
    std::vector<AsyncWebServerRequest *> streamClients;
    void handleMjpegStream(AsyncWebServerRequest *request);
    void setupWebServer();

public:
    void init();
    void update();

    void broadcastImg(uint8_t *img_buf, size_t img_len);
};

extern CamServer camServer;