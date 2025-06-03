#pragma once
#include <WebSocketsClient.h>

extern WebSocketsClient ws;
extern void (*onMessageCallback)(const String &message);

void wsclient_init();
void wsclient_update();
void wsclient_send_message(String &message);
void wsclient_on_message(void (*callback)(const String &message));
