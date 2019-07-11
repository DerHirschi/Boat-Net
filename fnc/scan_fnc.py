import time
import threading
import numpy as np
import matplotlib.cm as cm
from matplotlib import pyplot as plt
from etc.var import map_val
from etc.var import overflow_value
from etc.log import *
import shutil


class ScanSignals:
    def __init__(self, lte_stick, ardu):
        self.lte_stick = lte_stick
        self.arduino = ardu
        self.scanres3G = {}
        self.scanres4G = {}
        self.null_hdg = self.arduino.heading    # Flag has to set if delete self.scanres
        self.run_trigger = False                # Loop stopper
        # Plot Init #
        self.val_range = 1023
        self.N = int(self.val_range / (self.arduino.servo_max_angle - self.arduino.servo_min_angle) * 360)
        self.theta = np.arange(0.0, 2 * np.pi, 2 * np.pi / self.N)
        self.radii = []
        self.center = int((self.N - self.val_range) / 2)
        for i in range(self.N):
            self.radii.append(-1)
        self.width = np.pi / 4 * np.random.rand(self.N)
        for i in range(len(self.width)):
            self.width[i] = 6 / self.N

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
            self.get_lte_signals(duration=duration, hdg=val, resolution=resolution)
            n += step

    def get_lte_signals(self, hdg, resolution, duration=5):
        max_e_count = 7                 # If 6 times is None in sigs
        temp_sig = [0, 0, 0, 0]
        for n in range(duration):       # Get average of scan values
            e_count = 0
            while self.run_trigger:     # Sometimes got None value back
                sigs = self.lte_stick.get_string()
                if None in sigs:
                    e_count += 1
                elif e_count >= max_e_count:

                    duration -= 1
                    break
                else:
                    temp_sig = [temp_sig[0] + sigs[0], temp_sig[1] + sigs[1], temp_sig[2] + sigs[2], sigs[3]]
                    break

        if duration == 0:
            log("0 Signal !", 9)
            duration = 1
            temp_sig = [-20, -100, 0, 0]

        if temp_sig[3] in [2, 7]:
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

            if temp_sig[3] == 2:
                self.scanres3G = temp_res
            elif temp_sig[3] == 7:
                self.scanres4G = temp_res

    def scan_cycle(self, duration=2, timer=-1, resolution=32, lte_duration=7, net_mode=0, plot=False):
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
                    if plot:
                        print("PLOT")
                        threading.Thread(target=self.plot_scan, args=(net_mode,)).start()
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
                    if plot:
                        log("PLOT", 9)
                        threading.Thread(target=self.plot_scan, args=(net_mode,)).start()
                        # self.plot_scan(net_mode)

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

    def plot_scan(self, net_mode=2, signal_type=0):
        # TODO Werte glaetten ( evtl )
        # TODO Web Ausgabe in extra Class, extra thread ..

        # signal_type 1 = Plot Signal 'rsrq'
        # signal_type 2 = Plot Signal 'rsrp'
        # signal_type 3 = Plot Signal 'sinr'
        # signal_type 0 = Plot for all Signals
        # net_mode 2 = 3G
        # net_mode 3 = 4G
        scanres = {
            2: self.scanres3G,
            3: self.scanres4G
        }[net_mode]
        radii = self.radii
        width = self.width

        def _get_mode_config(mo, n_mo):
            return {
                2: {    # Null_val, colorrange, filename, mode
                    1: (20., 10, '3gecio-800x800', (mo - 1)),
                    2: (120., 60, '3grscp-800x800', (mo - 1)),
                    3: (110., 40, '3grssi-800x800', (mo - 1))
                }[mo],
                3: {    # Null_val, colorrange, filename, mode
                    1: (20., 10, '4grsrq-800x800', (mo - 1)),
                    2: (100., 20, '4grsrp-800x800', (mo - 1)),
                    3: (0., 20, '4gsinr-800x800', (mo - 1))
                }[mo]
            }[n_mo]
        conf = []
        if signal_type:
            conf.append(_get_mode_config(signal_type, net_mode))
        else:
            for c in range(3):
                conf.append(_get_mode_config((c + 1), net_mode))

        for con in conf:
            n_null, f_colo, o_name, signal_type = con
            # log("Start {}".format(con))
            max_ax = 0
            for i in range(self.N):
                if i in scanres:
                    cor_i = overflow_value((i + self.center), self.N)
                    _res = round((n_null + scanres[i][signal_type]), 2)
                    if _res > max_ax:
                        max_ax = _res
                    radii[cor_i] = _res
                    # log("radi> {} - i {} - sig {}".format(radii[cor_i], i, signal_type), 9)

            fig = plt.figure(figsize=(8, 8))
            ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
            # max_foo = int(max(radii))
            # c = np.ones((max_foo, max_foo)) + np.arange(max_foo).reshape(max_foo, 1)
            # ap = ax.pcolormesh(c)
            # ax.set_alpha(0.2)
            # plt.colorbar(ap)
            bars = ax.bar(self.theta, radii, width=width, bottom=0.0)
            for r, bar in zip(radii, bars):
                bar.set_facecolor(cm.jet(r / f_colo))
                bar.set_alpha(0.9)

            ax.set_rmin(-1)
            ax.set_rmax(max_ax)

            plt.savefig('/var/www/html/assets/images/' + o_name + '.png')
            plt.close(fig)
            shutil.copy('/var/www/html/assets/images/' + o_name + '.png',
                        '/var/www/html/assets/images/' + o_name + '-800x800' + '.png')

