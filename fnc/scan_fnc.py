import time
import threading
from etc.var import overflow_value, list_avg, map_val
from etc.log import log


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

        if temp_sig[3] in [2, 7]:
            if None not in temp_sig:
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

    @staticmethod
    def get_peak(scanres):     # TODO get peak signals in biggest range
        res, key = None, None
        for i in scanres.keys():
            if res:
                temp = scanres[i]
                if temp[0] > res[0]:
                    res, key = temp, i
            else:
                res, key = scanres[i], i
        return res, key

    @staticmethod
    def get_signal_peak_in_range(scanres, low_sig=-15):
        # lowest signals: 4G/RSRQ  = -15
        # lowest signals: 3G/EC/IO = -15
        temp_res = {}
        temp_arrays = []
        for key in scanres.keys():                # Drop all values below lowest signal
            if scanres[key][0] >= low_sig:
                temp_res[key] = scanres[key][0]

        temp_keys = sorted(temp_res.keys())

        i = 0
        flag_key = temp_keys[i]
        n = 0
        n_key = 0
        while n_key != len(temp_keys):          # put every range(array) in an array..
            if flag_key == n:                   # if value is in range
                if len(temp_arrays) == i:       # if new range
                    temp_arrays.append([n])
                else:                           # if range exist push next value to array
                    temp_arrays[i].append(n)
                n_key += 1
                if n_key < len(temp_keys):      # Break if all keys are irritated
                    flag_key = temp_keys[n_key] # pull nex key to temp
                else:
                    break
            else:                               # if value not in range
                i = len(temp_arrays)            # next range
            n += 1

        avg_res = {}                            # Return value dict
        for ra in temp_arrays:                  # Calculate average for each range
            temp = []
            for ke in ra:
                temp.append(scanres[ke][0])

            avg_res[round(list_avg(temp), 2)] = ra
        log(avg_res, 9)
        log(sorted(avg_res.keys()), 9)
        return avg_res                          # Return dict. Keys = avg values, value = list of servo hdg for range
