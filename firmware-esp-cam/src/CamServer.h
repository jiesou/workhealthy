#pragma once
#include <Arduino.h>
#include "lwip/netdb.h"
#include "lwip/sockets.h"
#include "lwip/netif.h"
#include "lwip/api.h"
#include <ESPAsyncWebServer.h>

class CamServer
{
private:
    AsyncWebServer *server;
    ip_addr_t udpServerIP = IPADDR4_INIT_BYTES(192,168,10,101);
    u16_t udpServerPort = 8099;
    std::vector<AsyncWebServerRequest *> streamClients;
    void handleMjpegStream(AsyncWebServerRequest *request);
    void setupConnection();
    void sendUdpWithNetconn(struct netconn *conn, const void *data, size_t len);
public:
    void init();
    void update();

    void broadcastImg(uint8_t *img_buf, size_t img_len);
};

extern CamServer camServer;