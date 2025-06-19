from .communication import CurrentCommunicator
import threading

POWER_RATIO = 19 / 17.12114

class CurrentProcessor:
    def __init__(self, sensor_url: str):
        self.communicator = CurrentCommunicator(sensor_url)
        self.frequency = 0.0
        self.power = 0.0

        self.thread = threading.Thread(
            target=self.parse_data, daemon=True).start()

    def parse_data(self):
        for data in self.communicator.read_data():
            if data is None:
                self.frequency = 0.0
                continue
            self.frequency = data['frequency']
            self.power = data['frequency'] * POWER_RATIO
