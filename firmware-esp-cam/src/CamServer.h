#pragma once
#include <Arduino.h>
#include <lwip/sockets.h>
#include <lwip/udp.h>
#include <ESPAsyncWebServer.h>

class CamServer
{
private:
    AsyncWebServer *server;
    struct sockaddr_in server_addr;
    u32_t udpServerIP = inet_addr("192.168.10.101");
    u16_t udpServerPort = 8099;
    std::vector<AsyncWebServerRequest *> streamClients;
    void handleMjpegStream(AsyncWebServerRequest *request);
    void setupConnection();

public:
    void init();
    void update();

    void broadcastImg(uint8_t *img_buf, size_t img_len);
};

extern CamServer camServer;