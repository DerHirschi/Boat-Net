import time
import threading
import numpy as np
import matplotlib.cm as cm
from matplotlib import pyplot as plt
from etc.var import map_val
from etc.var import overflow_value
from etc.log import *


class ScanSignals:
    def __init__(self, lte_stick, ardu):
        self.lte_stick = lte_stick
        self.arduino = ardu
        self.scanres = {}
        self.null_hdg = self.arduino.heading    # Flag has to set if delete self.scanres
        self.run_trigger = False                # Loop stopper
        # Plot Init #
        self.val_range = 1023
        self.N = int(self.val_range / (self.arduino.servo_max_angle - self.arduino.servo_min_angle) * 360)
        self.theta = np.arange(0.0, 2 * np.pi, 2 * np.pi / self.N)
        self.radii = []
        for i in range(self.N):
            self.radii.append(0)

    def get_hdg_diff_mapped(self):
        hdg = self.arduino.heading - self.arduino.lock_hdg
        return int(map_val(hdg, -360, 360, -self.N, self.N))

    def set_servo_hdg(self, val):
        # log("VAL " + str(val), 9)
        self.arduino.set_servo(servo=1, val=val)

    def scan_active(self, resolution=24, loop=None, duration=5):
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
            self.get_lte_signals(duration=duration, hdg=val, resolution=resolution)
            n += step

    def get_lte_signals(self, hdg, resolution, duration=5):
        temp = [0, 0, 0, 0]
        for n in range(duration):  # Get average of scan values
            while self.run_trigger:  # Sometimes got None value back
                sigs = self.lte_stick.get_string()
                if all(sigs):
                    temp = [temp[0] + sigs[0], temp[1] + sigs[1], temp[2] + sigs[2], sigs[3]]
                    break

        # range_begin = int(resolution / 2)
        # temp_res = temp
        # for z in range(resolution):
        #     i = hdg - range_begin + z
        #     i = overflow_value(i, self.N)
        #     temp_res = temp

        for ind in range(3):        # Calculate average for each founded value
            if hdg in self.scanres:
                temp[ind] = (self.scanres[hdg][(ind + 1)] + (temp[ind] / duration)) / 2
            else:
                temp[ind] = (temp[ind] / duration)

        # log("self.scanres[res_hdg] " + str([temp[3], temp[0], temp[1], temp[2]]) + "key " + str(hdg), 9)
        #                           mode,    rsrq,    rsrp,    sirn
        self.scanres[hdg] = [temp[3], temp[0], temp[1], temp[2]]

    def scan_cycle(self, duration=2, timer=-1, resolution=32, lte_duration=7):
        print("Run Scan Thread")
        lo = True
        self.run_trigger = True
        if timer != -1:
            ti = time.time()
            while self.run_trigger and self.arduino.run_trigger:
                print("Timed Thread")
                self.scan_active(resolution=resolution, loop=lo, duration=lte_duration)
                if lo:
                    lo = False
                else:
                    lo = True
                if (time.time() - ti) > timer:
                    break
        else:
            for n in range(duration):
                if self.run_trigger and self.arduino.run_trigger:
                    print("Scan Nr: " + str(n))
                    self.scan_active(resolution=resolution, loop=lo)
                    if lo:
                        lo = False
                    else:
                        lo = True
        self.run_trigger = False

    def run_scan_cycle_thread(self, duration=2, timer=-1, resolution=32, lte_duration=7):
        if self.arduino.run_trigger:
            return threading.Thread(target=self.scan_cycle, args=(duration, timer, resolution, lte_duration)).start()
        else:
            return False

    def get_peak(self):
        res, key = None, None
        for i in self.scanres.keys():
            if res:
                temp = self.scanres[i]
                if temp[0] > res[0]:
                    res, key = temp, i
                if temp[0] == res[0] and temp[1] > res[1]:     # Check 3G or 4G
                    res, key = temp, i
            else:
                res, key = self.scanres[i], i

        return res, key

    def plot_scan(self):
        # force square figure and square axes looks better for polar, IMO
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
        scanres = self.scanres

        tmp = 0
        n = 0
        for i in range(self.N):
            if len(scanres) == n:
                tmp = 0
            elif i in scanres:
                tmp = 20 + scanres[i][1]
                n += 1

            self.radii[i] = tmp

        width = np.pi / 4 * np.random.rand(self.N)
        for i in range(len(width)):
            width[i] = 6 / self.N
        bars = ax.bar(self.theta, self.radii, width=width, bottom=0.0)
        for r, bar in zip(self.radii, bars):
            bar.set_facecolor(cm.jet(r / 20.))
            bar.set_alpha(0.5)

        plt.savefig('/var/www/html/foo.png')

        plt.close(fig)
