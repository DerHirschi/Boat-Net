import serial
import threading
import time
from config import serial_ports, serial_baud


class ArduCom:
    def __init__(self):
        self.ser = None
        for p in serial_ports:
            try:
                self.ser = serial.Serial(p, serial_baud, 8, 'N', 1, timeout=1)
                print("Arduino found on: " + p)
            except serial.SerialException:
                self.ser = None
            if self.ser:
                break
        if not self.ser:
            raise ConnectionError

        # In Vars
        self.run_trigger = True     # Thread trigger .. Stop all Threads
        # Out Vars
        self.ack = -1               # ACK Pkt Flag ( -1 trigger f frei f. n. pkt )
        self.sac = True             # SAC Pkt Flag . If servo has final pos in servo slow speed mode
        self.heading = 0            # Heading get back from Ardu ( get after success full handshake)
        self.servo_min_angle = 0    # Angle get from Ardu Handshake. need to calculate scan angle
        self.servo_max_angle = 0    # Angle get from Ardu Handshake. need to calculate scan angle
        self.lock_hdg = 0           # Gimbal Lock Heading
        # Flags
        self.servo_on = False       # Servo toggle ( on/off Servo Gimbal on Ardu)
        self.servo_val = 512        # Temp Servo value
        # Handshake
        if self.get_handshake():
            print("Handshake successful..")
            # Receiver Thread
            threading.Thread(target=self.read_serial).start()
        else:
            print("Handshake failed !")
            self.run_trigger = False
            self.close()
            raise ConnectionAbortedError

    def close(self):
        self.ser.close()

    def get_handshake(self):
        flag = 'I'          # 'I' = 73
        ser_buffer = b''
        count = 0
        while self.run_trigger:
            temp_buffer = self.ser.read(1)
            if temp_buffer == b'\n':
                # parsing
                ser_buffer = ser_buffer.decode('UTF-8')
                if 'INITMIN' in ser_buffer:
                    # room for parsing init vars
                    # print(ser_buffer)
                    self.servo_min_angle = int(ser_buffer[(ser_buffer.find("INITMIN") + len("INITMIN")):(ser_buffer.find("INITMAX"))])
                    self.servo_max_angle = int(ser_buffer[(ser_buffer.find("INITMAX") + len("INITMAX")):(ser_buffer.find("HDG")) ])
                    self.ser.write(bytes((flag + str(int(True)) + '\n'), 'utf-8'))
                    ser_buffer = b''
                    count = 0
                elif 'ACK' in ser_buffer:                  # Init ACK
                    while self.ack != -1:
                        pass
                    if chr(int(ser_buffer[3:])) == flag:   # INIT completed
                        print('ACK-INIT-Recv :' + str(chr(int(ser_buffer[3:]))))
                        return True
                    ser_buffer = b''

                elif count > 4:
                    print(ser_buffer)
                    return False
                else:
                    print(ser_buffer)
                    ser_buffer = b''
                    count += 1
            elif len(ser_buffer) > 150:    # more than 150 bytes
                print(ser_buffer)
                return False
            else:
                ser_buffer += temp_buffer

            time.sleep(0.001)

    def read_serial(self):
        ser_buffer = b''
        while self.run_trigger:
            temp_buffer = self.ser.read(1)      # TODO try
            if temp_buffer == b'\n':
                # parsing
                ser_buffer = ser_buffer.decode('UTF-8')
                threading.Thread(target=self.parse_in_packet, args=(ser_buffer, )).start()
                ser_buffer = b''
            else:
                ser_buffer += temp_buffer

        self.close()

    def parse_in_packet(self, buffer_in):
        # print("Parser In:" + str(buffer_in))
        # ACK
        if 'ACK' in buffer_in:
            while self.ack != -1:
                pass
            self.ack = chr(int(buffer_in[3:]))
            # print('ACK-Recv :' + str(self.ack))
        # Heading
        elif 'HDG' in buffer_in:    # TODO make other smaller unique flag(maybe one byte). got lot of data form Ardu
            self.heading = float(buffer_in[3:])
        # Gimbal lock Heading
        elif 'LH' in buffer_in:     # TODO data behind flag. bool 1 or so
            self.lock_hdg = float(buffer_in[2:])
        # ACK if Servo is on Position
        elif 'SAC' in buffer_in:
            self.sac = True
        # Restart
        elif 'BSTRT' in buffer_in:
            print("Get Arduino Restart Trigger !!!")
            self.run_trigger = False
        else:
            print("Ardu: {}".format(buffer_in))

    def send_w_ack(self, _flag, _out_string):
        while self.ack != -1:
            if not self.run_trigger:
                break
        for _e in range(3):
            try:
                self.ser.write(bytes((_flag + _out_string + '\n'), 'utf-8'))
            except serial.SerialException:
                print("Error write to Arduion ...")
                self.run_trigger = False
                raise ConnectionError
            _e_count = 0
            while self.ack != _flag:
                if not self.run_trigger or _e_count >= 300:
                    print("ERROR: NO ACK in 3 sec")
                    break
                time.sleep(0.01)
                _e_count += 1
            if self.ack == _flag:
                self.ack = -1
                return True

        self.ack = -1
        print("ERROR: NO ACK with 3 trys")
        self.run_trigger = False
        raise ConnectionError

    def set_servo(self, servo=1, _val=512, _speed=1, new_gimbal_lock=False, wait_servo_confirm=False):
        flag = 'S'      # 'S' = 83
        out = ''
        if _speed != 1:
            self.sac = False
        if new_gimbal_lock:
            out += 'L'
        out += '{},{}:{}'.format((_val + 2000), _speed, servo)     # val+2000 to get - values
        self.servo_val = _val
        try:
            self.send_w_ack(flag, out)
        except ConnectionError:
            self.run_trigger = False
            return False

        if wait_servo_confirm:
            _e_count = 0
            while not self.sac and self.run_trigger:
                if _e_count < 300:               # wait for SAC or 300*0.1 sec (30 sec)
                    # TODO https://stackoverflow.com/questions/5568646/usleep-in-python/5568837
                    time.sleep(0.1)
                    # TODO wait just so long the servo needs to set + a few sec extra
                    _e_count += 1
                else:
                    print("ERROR: NO SAC in 30 sec")
                    return False
        return True

    def toggle_servos(self, switch=None):  # Servo toggle ( on/off Servo Gimbal on Ardu)
        flag = 'A'      # 'A' = 65
        if switch is None:
            self.servo_on = bool((int(self.servo_on) + 1) % 2)
        else:
            self.servo_on = switch
        self.send_w_ack(flag, str(int(self.servo_on)))

    def set_gimbal_lock_hdg(self):
        flag = 'B'  # 'B' = 66
        self.send_w_ack(flag, "")


