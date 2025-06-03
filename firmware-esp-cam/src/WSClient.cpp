#include "WSClient.h"

#define WS_SERVER_HOST "192.168.10.101"
#define WS_SERVER_PORT 8000

void WSClient::init() {
    ws.onEvent([this](WStype_t type, uint8_t *payload, size_t length) {
        switch (type) {
        case WStype_DISCONNECTED:
            Serial.println("WebSocket Disconnected");
            break;
        case WStype_CONNECTED:
            Serial.println("WebSocket Connected");
            ws.sendTXT("Hello from ESP32");
            break;
        case WStype_TEXT:
            Serial.printf("Message received: %s\n", payload);
            if (onMessageCallback) {
                onMessageCallback(String((char *)payload));
            }
            break;
        case WStype_BIN:
            Serial.printf("Binary message received, length: %d\n", length);
            break;
        case WStype_ERROR:
        case WStype_FRAGMENT_TEXT_START:
        case WStype_FRAGMENT_BIN_START:
        case WStype_FRAGMENT:
        case WStype_FRAGMENT_FIN:
            break;
        }
    });
    ws.begin(WS_SERVER_HOST, WS_SERVER_PORT, "/ws");
}
void WSClient::update() {
    ws.loop();
}
void WSClient::sendMessage(String &message) {
    ws.sendTXT(message);
}
void WSClient::onMessage(void (*callback)(const String &message)) {
    onMessageCallback = callback;
}

WSClient wsclient;