import serial


class ArduCom():
    def __init__(self):
        ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
        self.ser = None
        for p in ports:
            try:
                self.ser = serial.Serial(p, 115200, 8, 'N', 1, timeout=1)
                print("Arduino Connection found: " + p)
            except serial.SerialException as er:
                self.ser = None
                print("Arduino Connection Error: " + p)

            if(self.ser):
                break

        if(not self.ser):
            raise Exception

    def send2ardu(self, servo=1, val=512, speed=1):
        temp = "S{},{}:{}\n".format(val, speed, servo)
        self.ser.write(bytes(temp, 'utf-8'))
        # ser.reset_input_buffer()
        temp = b""
        while True:
            temp += self.ser.read(1)
            if(b"ACK 83" in temp):
                break

    def get_heading_ardu(self):
        self.ser.flushInput()
        while self.ser.read(1) != b"H":
            pass

        res = b""
        while True:
            res += self.ser.read(1)
            if(b"\n" in res):
                return int(res[:-1])
