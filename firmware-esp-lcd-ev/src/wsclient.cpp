#include "wsclient.h"
#include "lcd.h"

#define WS_SERVER_HOST "192.168.10.101"
#define WS_SERVER_PORT 8000
#define WS_SERVER_PATH "/monitor/MY/ws"

WebSocketsClient ws;
void (*onMessageCallback)(const String &message) = nullptr;
String fragmentBuffer = ""; // 用于存储分片消息

void wsclient_init()
{
    ws.setReconnectInterval(1000); // 设置重连间隔为 1 秒
    ws.enableHeartbeat(1000, 1000, 3); // 设置心跳间隔为 1 秒，超时为 1000 秒，断开重试次数为 3 次
    ws.onEvent([](WStype_t type, uint8_t *payload, size_t length)
               {
        Serial.printf("[WSClient] Event type: %d, length: %d\n", type, length);
        switch (type) {
        case WStype_DISCONNECTED:
            Serial.println("[WSClient] Disconnected");
            lcd_update_connect_status(false);
            break;
        case WStype_CONNECTED:
            Serial.println("[WSClient] Connected");
            lcd_update_connect_status(true);
            break;
        case WStype_TEXT:
            if (onMessageCallback) {
                onMessageCallback(String((char *)payload));
            }
            break;
        case WStype_BIN:
            break;
        case WStype_FRAGMENT_TEXT_START:
            fragmentBuffer = String((char *)payload); // 开始收集分片消息
            break;
        case WStype_FRAGMENT:
            fragmentBuffer += String((char *)payload); // 继续收集分片
            break;
        case WStype_FRAGMENT_FIN:
            fragmentBuffer += String((char *)payload); // 添加最后一个分片
            if (onMessageCallback)
            {
                onMessageCallback(fragmentBuffer); // 处理完整的消息
            }
            fragmentBuffer = ""; // 清空缓冲区
            break;
        case WStype_FRAGMENT_BIN_START:
            fragmentBuffer = "";
            // 重置缓冲区但不处理二进制分片
            break;
        case WStype_ERROR:
            Serial.printf("[WSClient] Error, type: %d, length: %d\n", type, length);
            break;
        } });
    ws.begin(WS_SERVER_HOST, WS_SERVER_PORT, WS_SERVER_PATH);
}
void wsclient_update()
{
    ws.loop();
}
void wsclient_send_message(const String &message)
{
    ws.sendTXT(message.c_str(), message.length());
}
void wsclient_on_message(void (*callback)(const String &message))
{
    onMessageCallback = callback;
}
