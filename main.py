from config import lte_stick_addi_1 as modem1
from fnc.huawei_com import LTEStick
from fnc.ardu_com import ArduCom
from fnc.scan_fnc import ScanSignals
import os
from etc.log import log
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
                self.ardu.set_servo(val=temp_ardu[1])               # Send last Servo value to Arduino
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
# Main calls to get Servo val back:
# main.scan.get_best_cell_hdg()
# main.scan.get_peak()   < TODO has to change to 3G/4G


main = Main(modem1)
if main.run_trigger:
    print("Main init")
    # main.ardu.set_servo(val=200)
    # main.ardu.set_gimbal_lock_hdg()
    main.ardu.set_servo(val=1023, speed=120, new_gimbal_lock=True)
    main.ardu.toggle_servos(True)
    time.sleep(2)
    try:
    # for m in [2, 3, 0]:
    #     main.lte.set_net_mode(m)
    #     print("Netmode {} gesetzt". format(m))
    #     try:
    #         time.sleep(40)

        # while main.run_trigger:
        if main.ardu.run_trigger:

            try:
                main.scan.scan_cycle(_resolution=32, _lte_duration=5, _duration=2, _net_mode=0)
            except ConnectionError:
            # while True:
            #     print(main.lte.get_string())
                print("Wird beendet ... Connection Error LTE")
                main.ardu.set_servo(val=512, speed=150, new_gimbal_lock=True)
                time.sleep(2)
                main.run_trigger = False
                # main.scan.plot_scan(1)
                # main.scan.plot_scan(2)
                # main.scan.plot_scan(3)
            # threading.Thread(target=main.scan.plot_scan, args=(2, )).start()
            # threading.Thread(target=main.scan.plot_scan, args=(3, )).start()
            # main.scan.get_signal_peak_in_range(main.scan.scanres3G, -10)
            # main.scan.get_signal_peak_in_range(main.scan.scanres4G, -6)

            log("2", 9)
            # main.scan.get_signal_arrays(2)    # called in scan.scan_cycle() after scan.scan_full_range()
            # TODO sig_array_3G & sig_array_4G fill gaps between cells(arrays)
            _cells = sorted(main.scan.sig_array_3G.keys(), reverse=True)
            if _cells:
                _scan_arr = main.scan.sig_array_3G[_cells[0]]
                log("_scan_arr 1 2 " + str(_scan_arr), 9)
                if _scan_arr:
                    log("Peak HDG of Array 2" + str(main.scan.get_peak_from_hgd_list(_scan_arr, 2)))
            log("", 9)
            log("3", 9)
            # main.scan.get_signal_arrays(2)    # called in scan.scan_cycle() after scan.scan_full_range()
            _cells = sorted(main.scan.sig_array_4G.keys(), reverse=True)
            log("_cells 4g",9)
            log(_cells,9)
            log("_cells 4g [0]", 9)
            log(_cells[0], 9)
            log("main.scan.sig_array_4G", 9)
            log(main.scan.sig_array_4G, 9)
            if _cells:
                _scan_arr = main.scan.sig_array_4G[_cells[0]]
                log("_scan_arr 1 3 " + str(_scan_arr), 9)
                if _scan_arr:
                    log("Peak HDG of Array 3" + str(main.scan.get_peak_from_hgd_list(_scan_arr, 3)))
            log("get_best_cell_hdg 1" + str(main.scan.get_best_cell_hdg(_mode=1)), 9)
            log("get_best_cell_hdg 2" + str(main.scan.get_best_cell_hdg(_mode=2)), 9)
            log("get_best_cell_hdg 3" + str(main.scan.get_best_cell_hdg(_mode=3)), 9)
            log("Plot Signals 2", 9)
            main.web.plot_lte_signals(2)
            time.sleep(1)
            log("Plot Signals 3", 9)
            main.web.plot_lte_signals(3)
            # FIXME
            # time.sleep(1)
            # log("Plot Arrays 2", 9)
            # main.web.plot_signal_arrays(2)
            # time.sleep(1)
            # log("Plot Arrays 3", 9)
            # main.web.plot_signal_arrays(3)
            # FIXME END
            # tmp = sorted(main.scan.scanres3G.keys())
            # for key in tmp:
            #     print("scanres3G - {} - {}".format(main.scan.scanres3G[key], key))
            # tmp = sorted(main.scan.scanres4G.keys())
            # for key in tmp:
            #     print("scanres4G - {} - {}".format(main.scan.scanres4G[key], key))

            main.scan.get_plmn_list()
            print("")
            print(main.scan.plmn_list)
            main.web.write_plmn_list2web()
            main.ardu.set_servo(val=512, speed=150, new_gimbal_lock=True)
            print("")
            print("Wird beendet ... ")
            time.sleep(2)
            main.run_trigger = False
    except KeyboardInterrupt:
        print("Wird beendet ... ")
        main.ardu.set_servo(val=512, speed=150, new_gimbal_lock=True)
        time.sleep(2)
        main.run_trigger = False



    # main.ardu.set_servo(val=512, speed=150)
    # time.sleep(2)
    # main.run_trigger = False
    # log(main.scan.scanres, 9)
    # tmp = sorted(main.scan.scanres.keys())
    # for key in tmp:
    #     log("{} - {}".format(main.scan.scanres[key], key), 9)

else:
    print("Main init failed. . .")
