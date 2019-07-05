import time
import threading
import numpy as np
import matplotlib.cm as cm
from matplotlib import pyplot as plt


class ScanSignals():
    def __init__(self, lte_stick, ardu):
        self.lte_stick = lte_stick
        self.arduino = ardu
        self.scanres = {}
        self.run_trigger = False       # Loop stopper
        # Plot Init #
        self.N = round((1024 / 225) * 360)
        self.theta = np.arange(0.0, 2 * np.pi, 2 * np.pi / self.N)
        self.radii = []
        for i in range(self.N):
            self.radii.append(0)

    def scan_complete(self, resolution=32, lte_duration=7, loop=None):
        self.run_trigger = True

        # TODO Werte zu 270 grad mappen + Heading vom ardu
        for i in range(int(1024/resolution)):
            val = int(i * resolution)
            if(loop):
                val = round(1024 - i * resolution)

            self.arduino.set_servo(servo=1, val=val)
            temp = [0, 0, 0]
            for n in range(lte_duration):     # Get average of scan values
                while True:                 # Sometimes got None value back
                    sigs = self.lte_stick.get_string()
                    if(all(sigs)):
                        temp = [temp[0] + sigs[0], temp[1] + sigs[1], temp[2] + sigs[2], sigs[3]]
                        # print("{} - {} {} {}".format(val, sigs[0], sigs[1], sigs[2]))
                        break
                if(not self.run_trigger):
                    print("EM Break")
                    break
            if(not self.run_trigger):
                print("EM Break")
                break
            for ind in range(3):
                if(val in self.scanres):
                    temp[ind] = (self.scanres[val][(ind + 1)] + (temp[ind] / lte_duration)) / 2
                else:
                    temp[ind] = (temp[ind] / lte_duration)
            #                    mode,    rsrq,    rsrp,    sirn
            self.scanres[val] = [temp[3], temp[0], temp[1], temp[2]]

        #self.run_trigger = False
        #print("{} \n".format(scanres[val]))

    def scan_cycle(self, duration=2, timer=-1, resolution=32, lte_duration=7):
        print("Run Scan Thread")
        lo = True
        if(timer != -1):
            self.run_trigger = True
            ti = time.time()
            while self.run_trigger:
                print("Timed Thread")
                self.scan_complete(resolution=resolution, loop=lo, lte_duration=lte_duration)
                if(lo):
                    lo = False
                else:
                    lo = True
                if((time.time() - ti) > timer):
                    break
        else:
            for n in range(duration):
                print("Scan Nr: " + str(n))
                self.scan_complete(resolution=resolution, loop=lo)
                if(lo):
                    lo = False
                else:
                    lo = True
        self.run_trigger = False

    def run_scan_cycle_thread(self, duration=2, timer=-1, resolution=32, lte_duration=7):
        return threading.Thread(target=self.scan_cycle, args=(duration, timer, resolution, lte_duration)).start()

    def get_peak(self):
        res, key = None, None
        for i in self.scanres.keys():
            if(res):
                temp = self.scanres[i]
                if(temp[0] > res[0]):
                    res, key = temp, i
                if(temp[0] == res[0] and temp[1] > res[1]):     # Check 3G or 4G
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
            if (len(scanres) == n):
                tmp = 0
            elif (i in scanres):
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
