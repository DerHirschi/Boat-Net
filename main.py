from fnc.huawei_com import LTEStick
from fnc.ardu_com import ArduCom
from fnc.scan_fnc import ScanSignals
from etc.log import log
from config import lte_stick_addi_1 as modem1
import threading
import time
import os


class Main:
    def __init__(self, modem):
        self.run_trigger = False
        self.ardu = None
        self.lte = None
        self.scan = None

        self.th_run = False         # Trigger to brake threaded loops
        self.thread = None          # Thread var to join the thread
        # TODO better loop timing system
        # Config TODO gather config vars in config.py
        self.scan_time_passive = 5      # Scan without move antenna. Just get signals # Check if active cell is visible
        self.new_servo_set_time = 10    # Check if none scanned range is visible
        self.web2data_timer = 500       # minimum wait if new plot can called
        self.scan_resolution = 32       # Resolution of scans
        self.scan_duration = 5          # Duration of scanned signals from LTE stick
        self.init_speed = 30            # Servo Speed for initialization scan
        self.cell_speed = 80            # Servo Speed for cell scan
        # Flags
        self.call_web2data = False
        self.c5 = time.time()
        self.cell_hdg_list = []
        # Arduino
        try:
            print("Arduino init")
            self.ardu = self.init_ardu()
            if self.ardu.run_trigger:
                self.ardu.set_servo(_val=512, _speed=30, wait_servo_confirm=False)
                self.ardu.toggle_servos(True)
                self.run_trigger = True
        except Exception as e:
            self.close("Arduino failed - " + str(e))

        if self.run_trigger:
            # LTE
            try:
                print("LTE init")
                self.lte = self.init_lte(modem)
            except Exception as e:
                self.close("LTE failed - " + str(e))
                self.run_trigger = False
            # Scan
            if self.run_trigger:
                print("Scan class init")
                self.scan = self.init_scan()
                self.scan.get_plmn_list()
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
                except Exception as e:
                    self.close("Arduino reinit failed !!! - " + str(e))
                    self.run_trigger = False
                    break
                self.ardu.servo_on = temp_ardu[0]                   # Write back temp values to Arduino
                self.ardu.toggle_servos(self.ardu.servo_on)         # Send last Servo state to Arduino
                self.ardu.set_servo(_val=temp_ardu[1])               # Send last Servo value to Arduino
                self.scan = self.init_scan()                        # Reinitialize Scan Class
                self.scan.scanres3G, \
                    self.scan.scanres4G, \
                    self.scan.null_hdg = temp_scan                  # Write back temp values to Scan Class
                # self.web = Data2Web(self.scan)                      # Reinitialize Web Output
            if not self.lte.run_trigger:                            # Check LTE Stick Error state
                _t = False
                try:
                    _t = self.lte.reboot()                              # Try to reboot Stick
                except Exception as e:
                    self.close("main.reinit_check() lte.reboot - " + str(e))
                if not _t:
                    self.close()
            time.sleep(1)
        self.close()

    def init_ardu(self):
        try:
            return ArduCom()
        except Exception as e:
            raise e

    def init_lte(self, modem):
        try:
            return LTEStick(modem)
        except Exception as e:
            raise e

    def init_scan(self):
        return ScanSignals(_lte_stick=self.lte, _ardu=self.ardu)

    def close(self, _e_in=None):
        if _e_in:
            print(str(_e_in))
        self.run_trigger = False
        self.th_run = False
        if self.scan:
            self.scan.run_trigger = False
        if self.ardu:
            self.ardu.run_trigger = False

    def data2web(self):
        self.c5 = time.time()
        self.call_web2data = False
        for _i in [2, 3]:
            self.scan.save_dict(_i)                    # Save data 2 File
        os.system('python3 data2web.py &')

    def go_strongest_cell(self, _net_mode=1, _speed=2):
        # _net_mode 1 = Auto
        _hdg = self.scan.get_best_cell_hdg(_mode=_net_mode)
        if _hdg:
            try:
                self.scan.set_servo_hdg(_val=_hdg[0], _speed=_speed)
                if _hdg[1] != self.lte.net_mode:
                    try:
                        self.lte.set_net_mode(_hdg[1])
                        self.cell_hdg_list = self.scan.get_cell_dict(self.lte.net_mode)[_hdg[2]]
                    except Exception as e:
                        # TODO just reboot LTE Stick
                        self.close("main.go_strongest_cell() set_net_mode -  " + str(e))
                else:
                    self.cell_hdg_list = self.scan.get_cell_dict(self.lte.net_mode)[_hdg[2]]
            except Exception as e:
                # TODO just reboot reinit Arduino
                self.close("go_strongest_cell() set_servo_hdg() - " + str(e))
        else:
            self.cell_hdg_list = []

    def chk_act_cell_vis(self):
        if not self.scan.check_if_in_vis_hdg(self.ardu.servo_val):
            log("chk_act_cell_vis ", 9)
            self.go_strongest_cell(_speed=self.cell_speed)

    def chk_sig_in_threshold(self):
        _sig = self.scan.get_scanres_dict(self.lte.net_mode)
        _sig = _sig[self.ardu.servo_val][0]
        if _sig < self.scan.get_threshold(self.lte.net_mode):
            log("chk_sig_in_threshold -- Trigger ", 9)
            log("chk_sig_in_threshold old cell hdg list  " + str(self.cell_hdg_list), 9)
            self.go_strongest_cell(_speed=self.cell_speed)
            log("chk_sig_in_threshold new cell hdg list  " + str(self.cell_hdg_list), 9)

    def chk_no_scanned_array(self):
        _t = False
        for _n in range(2):
            _le = len(self.scan.get_scanres_dict(self.lte.net_mode))
            if _le < self.scan.N:
                _le = int((self.scan.N - _le) / 2)   # FIXME _le get smaller and smaller. Also servo gets nervous
                _vis_hdg_not_scan = self.scan.get_not_scanned_vis_hdg(self.lte.net_mode)[0]
                if len(_vis_hdg_not_scan) >= _le:  # if more than 1/3 of not scanned array is visible, scan it
                    log("chk_no_scanned_array > " + str(_n), 9)
                    # if _n:
                    #     _vis_hdg_not_scan = _vis_hdg_not_scan[::-1]
                    try:
                        self.scan.scan_hdg_range(_vis_hdg_not_scan,
                                                 self.lte.net_mode,
                                                 self.cell_speed,
                                                 self.scan_resolution,
                                                 self.scan_duration)
                        if not _n:
                            try:
                                self.lte.switch_net_mode()
                            except Exception as e:
                                # TODO Reboot LTE Stick
                                self.close("main.chk_no_scanned_array()  switch_net_mode - " + str(e))
                                break
                        _t = True
                    except Exception as e:
                        self.close("main.chk_no_scanned_array() scan_hdg_range - " + str(e))
                        break

            if _t and _n:
                self.go_strongest_cell(_speed=self.cell_speed)
                self.call_web2data = True

    def cell_scan(self):
        log("cell_scan ", 9)
        try:
            self.scan.scan_hdg_range(self.cell_hdg_list,
                                     self.lte.net_mode,
                                     self.cell_speed,
                                     self.scan_resolution,
                                     self.scan_duration)
            self.go_strongest_cell(_speed=self.cell_speed)
            self.call_web2data = True
        except ConnectionError:
            self.close("main.cell_scan() scan_hdg_range ConnectionError")

    def pasv_scan(self):
        log("pasv_scan ", 9)
        self.scan.get_lte_signals_avg(self.ardu.servo_val,
                                      self.scan_resolution,
                                      self.scan_duration)
        self.scan.get_cells(self.lte.net_mode)
        self.chk_sig_in_threshold()

    @staticmethod
    def chk_loop_time(_time, _threshold):
        if (time.time() - _time) >= _threshold:
            return True
        return False

    def mode_init(self):
        log("mode_init ", 9)
        # Set run Trigger
        self.th_run = True
        # Switch servo to on
        self.ardu.toggle_servos(True)
        # Bring servo slowly to scan start pos
        try:
            self.ardu.set_servo(_val=1000, _speed=self.init_speed, wait_servo_confirm=True)
            # Scan slowly both Net Modes
            while self.run_trigger and self.th_run and not self.cell_hdg_list:
                try:
                    self.scan.scan_one_cycle(_resolution=self.scan_resolution,
                                             _lte_duration=self.scan_duration,
                                             _speed=self.init_speed)
                    # go slowly to strongest visible cell
                    self.go_strongest_cell(_speed=self.init_speed)
                    self.c5 = time.time()
                    self.data2web()
                except ConnectionError:
                    self.close("main.mode_init() scan.scan_one_cycle - ConnectionError")
        except ConnectionError:
            self.close("main.mode_init() ardu.set_servo - ConnectionError")

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
        # TODO Set configs before start
        self.mode_init()

        _c1 = time.time()        # scan_time_passiv
        _c3 = _c1                # new_servo_set_time
        while self.run_trigger and self.th_run:
            # Passive scan  # Check if active cell is visible
            if self.chk_loop_time(_c1, self.scan_time_passive):
                self.pasv_scan()                 # OK
                self.chk_act_cell_vis()
                _c1 = time.time()

            # Check if none scanned range is visible
            if self.chk_loop_time(_c3, self.new_servo_set_time):
                self.chk_no_scanned_array()
                _c3 = time.time()

            # Check data2web timer
            if self.chk_loop_time(self.c5, self.web2data_timer) and self.call_web2data:
                self.data2web()

            time.sleep(0.5)
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
        # TODO .. Make Button in Web-Gui .. maybe use Flask for Web-Gui .. .
        _inp = input("Do you want calibrate the accelerometer leveling parameters ? y/n> ")
        if 'Y' in _inp or 'y' in _inp:
            main.ardu.get_acc_cal_parm()

        try:
            main.mode_anchor()
        except KeyboardInterrupt:
            print('wird geschlossen')
            try:
                main.ardu.set_servo(1, 512, 70, False, True)
            except ConnectionError:
                print("Das wars E")
                main.close()

            print("Das wars")
            main.close()
