from fnc.huawei_com import LTEStick
from fnc.ardu_com import ArduCom
from fnc.scan_fnc import ScanSignals
import os
import threading
import time
import matplotlib as mpl
if not os.environ.get('DISPLAY'):     # Get an Error from python.tk.. Solution from:
    mpl.use('Agg')                    # https://forum.ubuntuusers.de/topic/python3-matplotlib-pyplot-funktioniert-nicht/
from web_gui.data2web import Data2Web # Python.tk import bug.


class Main:
    def __init__(self, modem):
        self.run_trigger = False
        self.ardu = None
        self.lte = None
        self.scan = None
        self.web = None
        # Arduino
        try:
            self.ardu = self.init_ardu()
            print("Arduino init")
            self.run_trigger = True
        except ConnectionError:
            print("Arduino failed")

        if self.run_trigger:
            # LTE
            try:
                print("LTE init")
                self.lte = self.init_lte(modem)
            except ConnectionError:
                print("LTE failed")
                self.run_trigger = False
            # Scan & Web
            if self.run_trigger:
                print("Scan class init")
                self.scan = self.init_scan()
                self.scan.get_plmn_list()
                self.web = Data2Web(self.scan)
                threading.Thread(target=self.reinit_check).start()

    def reinit_check(self):   # Reinitialisat if Arduino thread stops
        while self.run_trigger:
            if not self.ardu.run_trigger:
                print("Arduino Restart detected ....")
                self.scan.run_trigger = False                       # Close Scan Thread
                temp_ardu = self.ardu.servo_on, self.ardu.servo_val # Get temp values from old Ardu session
                temp_scan = self.scan.scanres3G, \
                    self.scan.scanres4G, \
                    self.scan.null_hdg                              # Get temp values from old Scan session
                try:                                                # Try reinitialize Arduino
                    self.ardu = self.init_ardu()
                except ConnectionError:
                    print("Arduino reinit failed !!!")
                    self.run_trigger = False
                    break
                self.ardu.servo_on = temp_ardu[0]                   # Write back temp values to Arduino
                self.ardu.toggle_servos(self.ardu.servo_on)         # Send last Servo state to Arduino
                self.ardu.set_servo(_val=temp_ardu[1])               # Send last Servo value to Arduino
                self.scan = self.init_scan()                        # Reinitialize Scan Class
                self.scan.scanres3G, \
                    self.scan.scanres4G, \
                    self.scan.null_hdg = temp_scan                  # Write back temp values to Scan Class
                self.web = Data2Web(self.scan)                      # Reinitialize Web Output
            time.sleep(1)
        self.ardu.run_trigger = False
        self.scan.run_trigger = False

    def init_ardu(self):
        try:
            return ArduCom()
        except (ConnectionError, ConnectionAbortedError) as e:
            raise ConnectionError('Connection Error') from e

    def init_lte(self, modem):
        try:
            return LTEStick(modem)
        except ConnectionError:
            raise ConnectionError

    def init_scan(self):
        return ScanSignals(_lte_stick=self.lte, _ardu=self.ardu)

    def mode_marina(self):
        # Moored boat at the marina without hdg changes
        # No GPS POS changed
        # Scan just passive after active scan
        # set self.ardu.toggle_servos(False) .. Antenna doesnt need to adjust
        # very slow servo adjustments because of noise
        # can use self.scan.get_peak() for get Antenna direction
        # get Signals all 30 sec or more
        # if Signal get lower than threshold switch to self.scan.get_best_cell_hdg() and get best cell
        # TODO get calculated Antenna pos back for scans (because Antenna is no more gimbaled)
        #  > self.ardu.toggle_servos(False)
        pass

    def mode_anchor(self):
        # Boat has dropped anchor .. HDG can changed
        # TODO No GPS POS changed
        # set self.ardu.toggle_servos(True)
        # slow servo adjustments because of noise
        # can use self.scan.get_best_cell_hdg() for get Antenna direction
        # Scan ( continuous all 30 - 60 sec) after active scan
        # if none scanned array is visible ( HDG has changed ), scan it
        # if active cell get badder, switch to next visible cell
        pass

    def mode_trip(self):
        # Boat is on trip .. HDG and Pos changed
        # set self.ardu.toggle_servos(True)
        # fast adjustments
        # Scan ( continuous all 5 - 15 sec ) after active scan
        # can use self.scan.get_best_cell_hdg() for get Antenna direction
        # if cell get badder scan slowly offset direction + and - org hdg
        # TODO offset scanning fnc
        # if none scanned array is visible ( HDG has changed ), scan it
        # if offset scanning results badder signals for cell, switch cell and go back to scanning
        # if no more cells available, make a new full scan
        # maybe a full scan all 1 - 2 km ??
        pass

# Main calls to get Servo val back:
# main.scan.get_best_cell_hdg()
# main.scan.get_peak()   < TODO has to change to 3G/4G
