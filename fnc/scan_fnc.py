import time
import threading
from etc.var import map_val
from etc.var import overflow_value
from etc.log import *


class ScanSignals:
    def __init__(self, lte_stick, ardu):
        self.lte_stick = lte_stick
        self.arduino = ardu
        self.scanres3G = {}
        self.scanres4G = {}
        self.plmn_list = []
        self.null_hdg = self.arduino.heading    # Flag has to set if delete self.scanres
        self.run_trigger = False                # Loop stopper
        # Plot Init #
        self.val_range = 1023
        self.N = int(self.val_range / (self.arduino.servo_max_angle - self.arduino.servo_min_angle) * 360)

    def get_plmn_list(self):
        plmn_list = self.lte_stick.get_plmn_list()
        res = []
        for net in plmn_list:
            res.append(net['FullName'])
        self.plmn_list = res

    def get_lte_signals_avg(self, hdg, resolution, duration=5):
        temp_sig = [0, 0, 0, 0]
        for n in range(duration):       # Get average of scan values
            sigs = self.lte_stick.get_string()
            if sigs:
                if None not in sigs:
                    temp_sig = [temp_sig[0] + sigs[0], temp_sig[1] + sigs[1], temp_sig[2] + sigs[2], sigs[3]]
                else:
                    if sigs[3]:
                        temp_sig[3] = sigs[3]
                    duration -= 1

        if temp_sig[3] in [2, 7]:
            if duration != 0:
                range_begin = int(resolution / 2)
                temp_res = {
                    2: self.scanres3G,
                    7: self.scanres4G
                }[temp_sig[3]]

                for z in range(resolution - 1):
                    i = (hdg - range_begin + z)
                    i = overflow_value(i, self.N)
                    if i in temp_res:       # Calculate average for each founded value
                        for ind in range(3):
                            temp_res[i][ind] = round(((temp_res[i][ind] + (temp_sig[ind] / duration)) / 2), 2)
                    else:
                        temp_res[i] = [round((temp_sig[0] / duration), 2),
                                       round((temp_sig[1] / duration), 2),
                                       round((temp_sig[2] / duration), 2)]
            else:
                temp_res = [None, None, None, temp_sig[3]]

            if temp_sig[3] == 2:
                self.scanres3G = temp_res
            elif temp_sig[3] == 7:
                self.scanres4G = temp_res

    def get_hdg_diff_mapped(self):
        hdg = self.arduino.heading - self.arduino.lock_hdg
        return int(map_val(hdg, -360, 360, -self.N, self.N))

    def set_servo_hdg(self, val):
        # log("VAL " + str(val), 9)
        self.arduino.set_servo(servo=1, val=val)

    def scan_full_range(self, resolution=24, loop=None, duration=5):
        val = 0
        n = 0
        n_max = self.val_range
        step = int(n_max / (resolution + 1))
        n_high = -self.get_hdg_diff_mapped() + n_max  # if loop:
        n_low = self.get_hdg_diff_mapped()            # if not loop:
        while n <= self.N and self.run_trigger:
            if loop:
                dif = self.get_hdg_diff_mapped() + n_max
                val = n_high - n
                if (n + n_low) >= dif:
                    break
            else:
                dif = n_max - self.get_hdg_diff_mapped()
                val = -n_low + n
                if (-n_low + n) >= dif:
                    break
            self.set_servo_hdg(val)
            time.sleep(0.1)
            self.get_lte_signals_avg(duration=duration, hdg=val, resolution=resolution)
            n += step

    def scan_cycle(self, duration=2, timer=-1, resolution=32, lte_duration=7, net_mode=0):
        # net_mode 0: scant 3G u 4G
        log("Run Scan Thread", 9)
        lo = True
        z = 0
        net_mode_switch = False
        if net_mode == 0:
            net_mode_switch = True
            net_mode = 2
            duration = duration * 2

        self.lte_stick.set_net_mode(net_mode)

        self.run_trigger = True
        if timer != -1:
            ti = time.time()
            while self.run_trigger and self.arduino.run_trigger:
                print("Timed Thread")
                self.scan_full_range(resolution=resolution, loop=lo, duration=lte_duration)
                if lo:
                    lo = False
                else:
                    z += 1
                    lo = True

                if net_mode_switch and z == 1:
                    z = 0
                    if net_mode == 2:
                        net_mode = 3
                    elif net_mode == 3:
                        net_mode = 2
                    try:
                        self.lte_stick.set_net_mode(net_mode)
                    except ConnectionError:
                        self.run_trigger = False
                        raise
                if (time.time() - ti) > timer:
                    break
        else:

            for n in range(duration):
                if not self.run_trigger or not self.arduino.run_trigger:
                    break
                log("Scan Nr: " + str(n), 9)
                self.scan_full_range(resolution=resolution, loop=lo)
                if lo:
                    lo = False
                else:
                    lo = True
                    z += 1

                if net_mode_switch and z == 1 and (duration - 1) != n:
                    z = 0
                    if net_mode == 2:
                        net_mode = 3
                    elif net_mode == 3:
                        net_mode = 2
                    log("Switch Band " + str(net_mode), 9)
                    try:
                        self.lte_stick.set_net_mode(net_mode)
                    except ConnectionError:
                        raise

        self.run_trigger = False

    def run_scan_cycle_thread(self, duration=2, timer=-1, resolution=32, lte_duration=7):
        if self.arduino.run_trigger:
            return threading.Thread(target=self.scan_cycle, args=(duration, timer, resolution, lte_duration)).start()
        else:
            return False

    def get_peak(self):
        res, key = None, None
        for i in self.scanres3G.keys():
            if res:
                temp = self.scanres3G[i]
                if temp[0] > res[0]:
                    res, key = temp, i
                if temp[0] == res[0] and temp[1] > res[1]:     # Check 3G or 4G
                    res, key = temp, i
            else:
                res, key = self.scanres3G[i], i

        return res, key
