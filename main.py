from config import lte_stick_addi_1 as modem1
from fnc.huawei_com import LTEStick
from fnc.ardu_com import ArduCom
from fnc.scan_fnc import ScanSignals
import time
import numpy as np
import matplotlib.cm as cm
from matplotlib import pyplot as plt


class Main():
    def __init__(self, modem):
        self.ardu = None
        self.lte = None
        try:
            self.ardu = self.init_ardu()
            print("Arduino init")
        except:
            self.ardu = None
        try:
            self.lte = self.init_lte(modem)
            print("LTE init")
        except:
            self.lte = None

        self.scan = None
        if(self.lte and self.ardu):
            print("Scan class init")
            self.scan = ScanSignals(lte_stick=self.lte, ardu=self.ardu)

    def init_ardu(self):
        try:
            return ArduCom()
        except:
            print("E1")
            return False

    def init_lte(self, modem):
        try:
            return LTEStick(modem)
        except Exception:
            print("E2")
            return False


def plot_scan(main_obj):
    # force square figure and square axes looks better for polar, IMO
    scanres = main_obj.scan.scanres
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
    N = round((1024 / 225) * 360)
    theta = np.arange(0.0, 2 * np.pi, 2 * np.pi / N)

    radii = []
    for i in range(N):
        radii.append(0)

    tmp = 0
    n = 0
    for i in range(N):
        if(len(scanres) == n):
            tmp = 0
        elif(i in scanres):
            tmp = 20 + scanres[i][1]
            n +=1

        radii[i] = tmp

    width = np.pi / 4 * np.random.rand(N)
    for i in range(len(width)):
        width[i] = 6 / N
    bars = ax.bar(theta, radii, width=width, bottom=0.0)
    for r, bar in zip(radii, bars):
        bar.set_facecolor(cm.jet(r / 20.))
        bar.set_alpha(0.5)

    plt.savefig('/var/www/html/foo.png')
    plt.close(fig)


main = Main(modem1)
if(main.scan):
    print("fertig")
else:
    print("fail")

#main.scan.run_scan_thread(duration=3, resolution=16)
#for i in range(4):
#    # print("wait")
#    time.sleep(20)
#    plot_scan(main)
try:
    while True:

        main.scan.scan_thread(resolution=4)
        plot_scan(main)
except KeyboardInterrupt:
    main.ardu.run_trigger = False
    main.scan.run_trigger = False
