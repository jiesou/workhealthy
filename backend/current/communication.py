from typing import Generator, TypedDict
import requests
import json
import time
import os


class CurrentCommunicator:
    response = None

    def open_connection(self):
        if self.response is None:
            try:
                self.response = requests.get(
                    self.sensor_url,
                    stream=True,
                    timeout=2
                )
                # 后端的 http 故障也直接抛出异常
                self.response.raise_for_status()
                print(f"[CurrentSensor] {self.sensor_url} 网络已连接")
            except Exception as e:
                print(f"[CurrentSensor] {self.sensor_url} 网络连接失败: {e}")
                self.response = None

    def __init__(self, sensor_url: str):
        self.sensor_url = sensor_url
        self.open_connection()

    class SensorData(TypedDict):
        millis: int
        sta_conn_status: int
        ip: str
        frequency: float
        frequency_overall: float
        btn_pressed: bool
        relay_state: int
        lbm_smart_info: int

    def read_data(self) -> Generator[SensorData, None, None]:
        """
        Generator that yields parsed sensor data as a dictionary with the following structure:
        {
            "millis": int,
            "sta_conn_status": int,
            "ip": str,
            "frequency": float,
            "frequency_overall": float, // overall 是最新 10 次采样的滑动中位数
            "btn_pressed": bool,
            "relay_state": int,
            "lbm_smart_info": int
        }
        """
        while True:
            try:
                for line in self.response.iter_lines(chunk_size=1, decode_unicode=True):
                    if line and line.startswith('data: '):
                        try:
                            yield json.loads(line[6:])
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"[CurrentSensor] 网络连接故障: {e}")
                time.sleep(1)
                self.response = None
                self.open_connection()
                yield None
                continue
