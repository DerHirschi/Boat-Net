import serial
import threading
import time
from config import serial_ports, serial_baud


class ArduCom():
    def __init__(self):
        self.ser = None
        for p in serial_ports:
            try:
                self.ser = serial.Serial(p, serial_baud, 8, 'N', 1, timeout=1)
                print("Arduino found on: " + p)
            except serial.SerialException:
                self.ser = None
            if(self.ser):
                break
        if(not self.ser):
            raise Exception

        # In Vars
        self.run_trigger = True     # Thread trigger .. Stop all Threads
        self.fast_recv = False      # Fast receiver loop
        # Out Vars
        self.ack = -1               # Ack Pkt Flag ( -1 trigger f frei f. n. pkt )
        self.heading = 0            # Heading get back from Ardu ( has to requested on Ardu)
        # Handshake
        if(self.get_handshake()):
            print("Handshake successful..")
            # Receiver Thread
            self.receiver = threading.Thread(target=self.read_serial).start()
        else:
            print("Handshake failed !")
            raise Exception("Handshake failed")

    def close(self):
        self.ser.close()

    def get_handshake(self):
        ser_buffer = b''
        run = True
        count = 0
        while run:
            temp_buffer = self.ser.read(1)
            if (temp_buffer == b'\n'):
                # parsing
                ser_buffer = ser_buffer.decode('UTF-8')
                if('INITMIN' in ser_buffer):
                    # room for init vars
                    return True
                elif(count > 3):
                    print(ser_buffer)
                    return False
                else:
                    print(ser_buffer)
                    ser_buffer = b''
                    count += 1
            elif(len(ser_buffer) > 150):    # more than 150 bytes
                print(ser_buffer)
                return False
            else:
                ser_buffer += temp_buffer

            time.sleep(0.001)

    def read_serial(self):
        ser_buffer = b''
        while self.run_trigger:
            temp_buffer = self.ser.read(1)
            if(temp_buffer == b'\n'):
                # parsing
                ser_buffer = ser_buffer.decode('UTF-8')
                threading.Thread(target=self.parse_in_packet, args=(ser_buffer, )).start()
                # self.parse_in_packet(ser_buffer.decode('UTF-8'))
                ser_buffer = b''
            else:
                ser_buffer += temp_buffer
            if(not self.fast_recv):
                time.sleep(0.001)
        self.close()

    def parse_in_packet(self, buffer_in):
        print("Parser In:" + str(buffer_in))
        # ACK
        if('ACK' in buffer_in):
            while self.ack != -1:
                pass
            self.ack = chr(int(buffer_in[3:]))
            print('ACK-Recv :' + str(self.ack))
        # Heading
        elif('HDG' in buffer_in):
            self.heading = float(buffer_in[3:])
            #print(self.heading)
        else:
            print(buffer_in)

    def send_w_ack(self, flag, out_string):
        while self.ack != -1:
            pass
        self.ser.write(bytes((flag + out_string + '\n'), 'utf-8'))
        while self.ack != flag:
            pass
        self.ack = -1

    def set_servo(self, servo=1, val=512, speed=1, wait_servo_confirm=False):
        flag = 'S'      # 'S' = 83
        out = "{},{}:{}".format(val, speed, servo)
        self.send_w_ack(flag, out)

        # TODO entweder via ACK o extra Flag parsing
        if(wait_servo_confirm):
            pass

    def toggle_servos(self, switch):
        flag = 'A'      # 'A' = 65
        self.send_w_ack(flag, str(int(switch)))

