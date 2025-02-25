import obd

class OBDConnector:
    def __init__(self):
        self.connection = None
        self.rpm = 0.0
        self.speed = 0.0

    def connect(self, port=None):
        try:
            self.connection = obd.OBD(port)
            return self.connection.is_connected()
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def update_data(self):
        if self.connection and self.connection.is_connected():
            # RPM (PID 0x0C)
            response = self.connection.query(obd.commands.RPM)
            self.rpm = response.value.magnitude if not response.is_null() else 0.0

            # Speed (PID 0x0D)
            response = self.connection.query(obd.commands.SPEED)
            self.speed = response.value.magnitude if not response.is_null() else 0.0

    def close(self):
        if self.connection:
            self.connection.close()