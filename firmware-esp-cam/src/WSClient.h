#pragma once
#include <WebSocketsClient.h>
class WSClient
{
public:
    void init();
    void update();
    void sendMessage(String &message);
    void onMessage(void (*callback)(const String &message));

private:
    WebSocketsClient ws;
    void (*onMessageCallback)(const String &message) = nullptr;
};
extern WSClient wsclient;