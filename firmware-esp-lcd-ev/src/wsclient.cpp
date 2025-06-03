#include "wsclient.h"
#define WS_SERVER_HOST "192.168.10.101"
#define WS_SERVER_PORT 8000

WebSocketsClient ws;
void (*onMessageCallback)(const String &message) = nullptr;

void wsclient_init() {
    ws.onEvent([](WStype_t type, uint8_t *payload, size_t length) {
        switch (type) {
        case WStype_DISCONNECTED:
            Serial.println("[WSClient] Disconnected");
            break;
        case WStype_CONNECTED:
            Serial.println("[WSClient] Connected");
            break;
        case WStype_TEXT:
            if (onMessageCallback) {
                onMessageCallback(String((char *)payload));
            }
            break;
        case WStype_BIN:
            Serial.printf("[WSClient] Binary message received, length: %d\n", length);
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
void wsclient_update() {
    ws.loop();
}
void wsclient_send_message(String &message) {
    ws.sendTXT(message);
}
void wsclient_on_message(void (*callback)(const String &message)) {
    onMessageCallback = callback;
}
