from fnc.huawei_com import LTEStick
from fnc.ardu_com import ArduCom
from fnc.scan_fnc import ScanSignals
from config import lte_stick_addi_1 as modem1
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

        self.th_run = False         # Trigger to brake threaded loops
        self.thread = None          # Thread var to join the thread
        # Arduino
        try:
            print("Arduino init")
            self.ardu = self.init_ardu()
            self.ardu.set_servo(_val=512, _speed=200, wait_servo_confirm=True)
            self.ardu.toggle_servos(True)
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

    def close(self, _e_in=None):
        if _e_in:
            print(str(_e_in))
        self.run_trigger = False
        self.th_run = False
        self.scan.run_trigger = False
        self.ardu.run_trigger = False

    def go_strongest_cell(self, _net_mode=1, _speed=2):
        # _net_mode 1 = Auto
        _hdg = self.scan.get_best_cell_hdg(_mode=_net_mode)
        self.lte.set_net_mode(_hdg[1])
        if _hdg:
            self.scan.set_servo_hdg(_val=_hdg[0], _speed=_speed)
            return _hdg[2]
        else:
            return False

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
        # TODO if get no results after initialization scan
        # set self.ardu.toggle_servos(True)
        # slow servo adjustments because of noise
        # can use self.scan.get_best_cell_hdg() for get Antenna direction
        # Scan ( continuous all 30 - 60 sec) after active scan
        # if none scanned array is visible ( HDG has changed ), scan it
        # if active cell get badder, switch to next visible cell

        # Config TODO gather config vars in config.py
        scan_time_passiv = 30       # Scan without move antenna. Just get signals
        scan_time_cell = 60         # Scan cell with move antenna. Just get signals
        new_servo_set_time = 10     # Time if check if a stronger cell is available
        scan_resolution = 40        # Resolution of scans
        scan_durration = 5          # Duration of scanned signals from LTE stick
        init_speed = 250            # Servo Speed for initialization scan
        cell_speed = 400            # Servo Speed for cell scan

        # Set run Trigger
        self.th_run = True
        # Switch servo to on
        self.ardu.toggle_servos(True)
        # Bring servo slowly to scan start pos
        self.ardu.set_servo(_val=1000, _speed=init_speed, wait_servo_confirm=True)
        # Scan slowly both Net Modes
        try:
            self.scan.scan_one_cycle(_resolution=scan_resolution, _lte_duration=scan_durration, _speed=init_speed)
        except ConnectionError:
            self.close("self.scan.scan_one_cycle ConnectionError in main.mode_anchor()")
        # go slowly to strongest visible cell
        _cell_key = self.go_strongest_cell(_speed=init_speed)
        if _cell_key:       # No results in first scan
            _c1 = 0
            _c2 = 0
            _c3 = 0
            while self.run_trigger and self.th_run:
                if _c1 > scan_time_passiv:      # Passive scan
                    self.scan.get_lte_signals_avg(self.ardu.servo_val, scan_resolution,)
                    _c1 = 0
                else:
                    _c1 += 1

                if _c2 > scan_time_cell:        # Active scan
                    _hdg_list = self.scan.get_cell_dict(self.lte.net_mode)
                    _hdg_list = _hdg_list[_cell_key]
                    self.scan.vis_hdg_of_list(_hdg_list)
                    self.scan.scan_hdg_range(_hdg_list,
                                             self.lte.net_mode,
                                             cell_speed,
                                             scan_resolution,
                                             scan_durration)
                    _c2 = 0
                else:
                    _c2 += 1

                # Check if stronger cell is available
                if _c3 > new_servo_set_time:
                    _cell_key = self.go_strongest_cell(_speed=cell_speed)
                    _c3 = 0
                else:
                    _c3 += 1

                # Check if none scanned range is visible
                _le = len(self.scan.get_scanres_dict(self.lte.net_mode))
                if _le < self.scan.N:

                    _le = int(round((self.scan.N - _le) / 3))
                    _vis_hdg_not_scan = self.scan.get_not_scanned_vis_hdg(self.lte.net_mode)
                    # print("not scanned vis   " + str(_vis_hdg_not_scan))
                    # FIXME .. something is wrong here .. but .. sunrise = bedtime
                    if len(_vis_hdg_not_scan) > _le:        # if more than 1/3 of not scanned array is visible, scan it
                        # print("more than 1/3 vis")
                        self.scan.scan_hdg_range(_vis_hdg_not_scan,
                                                 self.lte.net_mode,
                                                 cell_speed,
                                                 scan_resolution,
                                                 scan_durration)
                        _cell_key = self.go_strongest_cell(_speed=cell_speed)
                time.sleep(1)

        self.th_run = False

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


if __name__ == '__main__':
    # first attempt
    main = Main(modem1)
    if main.run_trigger:
        try:
            main.mode_anchor()
        except KeyboardInterrupt:
            print('wird geschlossen')
            print('Plot 1 wird erstellt')
            main.web.plot_lte_signals(2)
            print('Plot 1 wird erstellt')
            main.web.plot_lte_signals(3)
            print("Das wars")
            main.close()
