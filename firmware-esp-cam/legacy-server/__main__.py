import json
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI()

# Global variables
connected_clients: List[WebSocket] = []
esp32_client: Optional[WebSocket] = None


def is_valid_jpeg(data: bytes) -> bool:
    """Validate if the bytes represent a valid JPEG image"""
    if len(data) < 4:
        return False
    # JPEG files start with 0xFFD8 and end with 0xFFD9
    return (data[0] == 0xFF and data[1] == 0xD8 and
            data[-2] == 0xFF and data[-1] == 0xD9)


async def broadcast_image(data: bytes):
    """Broadcast image data to all connected HTML clients"""
    if not connected_clients:
        return

    metadata = {"type": "image", "length": len(data)}

    disconnected = []
    for client in connected_clients:
        try:
            await client.send_text(json.dumps(metadata))
            await client.send_bytes(data)
        except:
            disconnected.append(client)

    # Remove disconnected clients
    for client in disconnected:
        if client in connected_clients:
            connected_clients.remove(client)


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    global esp32_client

    await websocket.accept()

    # Check protocol to identify client type
    protocol = websocket.headers.get("sec-websocket-protocol")

    if protocol == "ESP32":
        print("ESP32 client connected")
        esp32_client = websocket

        try:
            while True:
                data = await websocket.receive_bytes()
                
                # Only handle JPEG images, ignore audio data
                if is_valid_jpeg(data):
                    print(f"Broadcasting image: {len(data)} bytes")
                    await broadcast_image(data)

        except WebSocketDisconnect:
            print("ESP32 client disconnected")
            esp32_client = None

    else:
        print("HTML client connected")
        connected_clients.append(websocket)

        try:
            while True:
                # Keep connection alive, but don't need to handle any commands
                message = await websocket.receive_text()
                # Just echo back for debugging if needed
                print(f"Received from client: {message}")

        except WebSocketDisconnect:
            print("HTML client disconnected")
            if websocket in connected_clients:
                connected_clients.remove(websocket)


@app.get("/client")
async def get_client():
    return FileResponse("legacy-server/client.html")


@app.get("/")
async def root():
    return {"message": "Simple image streaming server"}


if __name__ == "__main__":
    uvicorn.run("legacy-server.__main__:app", host="0.0.0.0", port=8080)