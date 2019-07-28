import serial
import threading
import time
from config import serial_ports, serial_baud
from six.moves import cPickle as Pickle         # for performance


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
        self.p_in = False           # Trigger for getting mag parameters from ardu
        self.is_busy = 0            # Trigger get from Ardu, can receive packets or not
        # Configs
        self.conf_file = 'fnc/configs.pkl'
        # Accelerometer
        self.acc_roll_cal = .0      # Calibrating parameter for accelerometer roll
        self.acc_pitch_cal = .0     # Calibrating parameter for accelerometer pitch
        # Magnetometer
        self.Mag_x_offset = 0       # Hard iron
        self.Mag_y_offset = 0       # Hard iron
        self.Mag_z_offset = 0       # Hard iron
        self.Mag_x_scale = .0       # Soft iron
        self.Mag_y_scale = .0       # Soft iron
        self.Mag_z_scale = .0       # Soft iron
        self.ASAX = .0              # ASA
        self.ASAY = .0              # ASA
        self.ASAZ = .0              # ASA
        # Handshake
        if self.get_handshake():
            print("Handshake successful..")
            # Receiver Thread
            threading.Thread(target=self.read_serial).start()
            try:
                self.load_configs()
            except KeyError or FileNotFoundError:
                pass
            print("Ardu Init complete..")
        else:
            print("Handshake failed !")
            self.run_trigger = False
            self.close()

    def close(self):
        self.ser.close()

    def load_configs(self):
        try:
            with open(self.conf_file, 'rb') as f:
                _di = Pickle.load(f)
                if _di:
                    self.acc_roll_cal = _di['acc_roll']
                    self.acc_pitch_cal = _di['acc_pitch']
                    self.Mag_x_offset = _di['Mag_x_offset']
                    self.Mag_y_offset = _di['Mag_y_offset']
                    self.Mag_z_offset = _di['Mag_z_offset']
                    self.Mag_x_scale = _di['Mag_x_scale']
                    self.Mag_y_scale = _di['Mag_y_scale']
                    self.Mag_z_scale = _di['Mag_z_scale']
                    self.ASAX = _di['ASAX']
                    self.ASAY = _di['ASAY']
                    self.ASAZ = _di['ASAZ']

            print("Send ACC leveling parameters..")
            self.set_acc_cal_parm()
            print("ACC leveling parameters sended")
        except FileNotFoundError or KeyError as e:
            self.get_acc_cal_parm()
            self.get_mag_parm()
            print(e)

    def save_configs(self):
        _di = {
            'acc_roll': self.acc_roll_cal,
            'acc_pitch': self.acc_pitch_cal,
            'Mag_x_offset': self.Mag_x_offset,
            'Mag_y_offset': self.Mag_y_offset,
            'Mag_z_offset': self.Mag_z_offset,
            'Mag_x_scale': self.Mag_x_scale,
            'Mag_y_scale': self.Mag_y_scale,
            'Mag_z_scale': self.Mag_z_scale,
            'ASAX': self.ASAX,
            'ASAY': self.ASAY,
            'ASAZ': self.ASAZ,
        }
        with open(self.conf_file, 'wb') as _f:
            Pickle.dump(_di, _f)

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
                        # print('ACK-INIT-Recv :' + str(chr(int(ser_buffer[3:]))))
                        return True
                    ser_buffer = b''
                elif '.' in ser_buffer:
                    print(ser_buffer)
                    ser_buffer = b''
                    count = 0
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
            while self.ack != -1 and self.run_trigger:
                pass
            self.ack = chr(int(buffer_in[3:]))
            # print('ACK-Recv :' + str(self.ack))
        # Heading
        elif '$' in buffer_in:
            _temp = buffer_in[1:]
            # print("HDG: " + str(_temp))
            if _temp.replace(".", "", 1).isdigit():
                self.heading = float(_temp)
        # Gimbal lock Heading
        elif 'LH' in buffer_in:
            self.lock_hdg = float(buffer_in[2:])
        # Accelerometer calibrating parameters
        elif 'CA' in buffer_in:
            # TODO CRC for this shit . . .
            # CA-0.71P-3.01R
            self.acc_pitch_cal = float(buffer_in[2:(buffer_in.find("P"))])
            self.acc_roll_cal = float(buffer_in[(buffer_in.find("P") + 1):(buffer_in.find("R"))])
            self.save_configs()
        elif 'CM' in buffer_in:
            # TODO CRC for this shit . . .
            # CM40a-236b147c1.01d0.98e1.01f1.18g1.18h1.14i
            self.Mag_x_offset = int(buffer_in[2:(buffer_in.find("a"))])
            self.Mag_y_offset = int(buffer_in[(buffer_in.find("a") + 1):(buffer_in.find("b"))])
            self.Mag_z_offset = int(buffer_in[(buffer_in.find("b") + 1):(buffer_in.find("c"))])
            self.Mag_x_scale = float(buffer_in[(buffer_in.find("c") + 1):(buffer_in.find("d"))])
            self.Mag_y_scale = float(buffer_in[(buffer_in.find("d") + 1):(buffer_in.find("e"))])
            self.Mag_z_scale = float(buffer_in[(buffer_in.find("e") + 1):(buffer_in.find("f"))])
            self.ASAX = float(buffer_in[(buffer_in.find("f") + 1):(buffer_in.find("g"))])
            self.ASAY = float(buffer_in[(buffer_in.find("g") + 1):(buffer_in.find("h"))])
            self.ASAZ = float(buffer_in[(buffer_in.find("h") + 1):(buffer_in.find("i"))])
            self.save_configs()
            self.p_in = True
        # ACK if Servo is on Position
        elif 'SAC' in buffer_in:
            self.sac = True
        # RCV Trigger if ardu can receive packets or is busy
        elif 'BSY' in buffer_in:
            self.is_busy = int(buffer_in[3:4])
        # Restart
        elif 'BSTRT' in buffer_in:
            print("Get Arduino Restart Trigger !!!")
            self.run_trigger = False
        else:
            print("Ardu: {}".format(buffer_in))

    def send_w_ack(self, _flag, _out_string):
        while (self.ack != -1 or self.is_busy) and self.run_trigger:
            # if (self.ack == -1 and not self.is_busy) or not self.run_trigger:
                # break
            time.sleep(0.001)
        if self.run_trigger:
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
            print("ERROR: NO ACK with 3 try´s")
            self.run_trigger = False
            raise ConnectionError

    def set_servo(self, _servo=1, _val=512, _speed=1, _new_gimbal_lock=False, wait_servo_confirm=False):
        _flag = 'S'      # 'S' = 83
        _out = ''
        if _speed != 1:
            self.sac = False
        if _new_gimbal_lock:
            _out += 'L'
        _out += '{},{}:{}'.format((_val + 2000), _speed, _servo)     # val+2000 to get - values
        try:
            self.send_w_ack(_flag, _out)
            self.servo_val = _val
        except ConnectionError:
            raise

        if wait_servo_confirm:
            _e_count = 0
            while not self.sac and self.run_trigger:
                if _e_count < 600:               # wait for SAC or 300*0.1 sec (30 sec)
                    # TODO https://stackoverflow.com/questions/5568646/usleep-in-python/5568837
                    time.sleep(0.1)
                    # TODO wait just so long the servo needs to set + a few sec extra
                    _e_count += 1
                else:
                    print("ERROR: NO SAC in 60 sec")
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

    # Ardu set automatic accelerometer level parameters end send it back
    def get_acc_cal_parm(self):
        flag = 'C'  # 'C' = 67
        self.send_w_ack(flag, 'A')      # 'A' accelerometer

    def set_acc_cal_parm(self):
        flag = 'C'  # 'C' = 67
        _str = 'A' + str(self.acc_pitch_cal) + 'P' + str(self.acc_roll_cal) + 'R'
        self.send_w_ack(flag, _str)

    def get_mag_parm(self):
        flag = 'C'  # 'C' = 67
        self.send_w_ack(flag, 'P')      # 'P' magnetometer parameter
        self.p_in = False

    def calibrate_mag(self):
        flag = 'C'  # 'C' = 67
        self.send_w_ack(flag, 'M')      # 'M' magnetometer
        self.print_mag_parm()

    def print_mag_parm(self):
        self.get_mag_parm()
        while not self.p_in:
            time.sleep(0.001)
        print("------------------------------------------------")
        print("Hard-Iron:")
        print("Mag_x_offset: {}, "
              "Mag_y_offset: {}, "
              "Mag_z_offset: {}".format(self.Mag_x_offset,
                                        self.Mag_y_offset,
                                        self.Mag_z_offset))
        print("Soft-Iron:")
        print("Mag_x_scale: {}, "
              "Mag_y_scale: {}, "
              "Mag_z_scale: {}".format(self.Mag_x_scale,
                                       self.Mag_y_scale,
                                       self.Mag_z_scale))
        print("ASA:")
        print("ASAX: {}, "
              "ASAY: {}, "
              "ASAZ: {}".format(self.ASAX,
                                self.ASAY,
                                self.ASAZ))
        print("------------------------------------------------")


