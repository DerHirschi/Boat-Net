from config import lte_stick_addi_1 as modem1
from fnc.huawei_com import LTEStick
from fnc.ardu_com import ArduCom
from fnc.scan_fnc import ScanSignals
from etc.log import log
import threading
import time


class Main:
    def __init__(self, modem):
        self.run_trigger = False
        self.ardu = None
        self.lte = None
        self.scan = None
        try:
            self.ardu = self.init_ardu()
            print("Arduino init")
            self.run_trigger = True
        except ConnectionAbortedError:
            print("Arduino failed")

        if self.run_trigger:
            try:
                self.lte = self.init_lte(modem)
                print("LTE init")
            except ConnectionError:
                print("LTE failed")
                self.run_trigger = False

            if self.run_trigger:
                print("Scan class init")
                self.scan = self.init_scan()
                threading.Thread(target=self.reinit_check).start()

    def reinit_check(self):   # Reinitialisat if Arduino thread stops
        while self.run_trigger:
            if not self.ardu.run_trigger:
                print("Arduino Restart detected ....")
                self.scan.run_trigger = False                       # Close Scan Thread
                temp_ardu = self.ardu.servo_on, self.ardu.servo_val # Get temp values from old Ardu session
                temp_scan = self.scan.scanres, self.scan.null_hdg   # Get temp values from old Scan session
                try:                                                # Try reinitialize Arduino
                    self.ardu = self.init_ardu()
                except:
                    print("Arduino reinit failed !!!")
                    self.run_trigger = False
                    break
                self.scan = self.init_scan()                        # Reinitialize Scan Class
                self.ardu.servo_on = temp_ardu[0]                   # Write back temp values to Arduino
                self.scan.scanres, self.scan.null_hdg = temp_scan   # Write back temp values to Scan Class
                self.ardu.toggle_servos(self.ardu.servo_on)         # Send last Servo state to Arduino
                self.ardu.set_servo(val=temp_ardu[1])               # Send last Servo value to Arduino
            time.sleep(1)
        self.ardu.run_trigger = False
        self.scan.run_trigger = False

    def init_ardu(self):
        try:
            return ArduCom()
        except ConnectionAbortedError:
            raise ConnectionAbortedError

    def init_lte(self, modem):
        try:
            return LTEStick(modem)
        except ConnectionError:
            raise ConnectionError

    def init_scan(self):
        return ScanSignals(lte_stick=self.lte, ardu=self.ardu)


main = Main(modem1)
if main.run_trigger:
    print("Main init")

    # main.ardu.set_servo(val=200)
    main.ardu.toggle_servos(True)
    try:
        while main.run_trigger:
            if main.ardu.run_trigger:
                main.scan.scan_cycle(resolution=24, lte_duration=7)
                # main.scan.plot_scan()
                threading.Thread(target=main.scan.plot_scan).start()
                # tmp = sorted(main.scan.scanres.keys())
                # for key in tmp:
                #     log("{} - {}".format(main.scan.scanres[key], key), 9)

                # log("\n")

    except KeyboardInterrupt:
        main.run_trigger = False

    main.run_trigger = False
    # log(main.scan.scanres, 9)
    # tmp = sorted(main.scan.scanres.keys())
    # for key in tmp:
    #     log("{} - {}".format(main.scan.scanres[key], key), 9)

else:
    print("Main init failed. . .")
