from config import lte_stick_addi_1 as modem1
from fnc.huawei_com import LTEStick
from fnc.ardu_com import ArduCom
from fnc.scan_fnc import ScanSignals
from etc.log import log
import threading


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
main.ardu.set_servo()
main.ardu.toggle_servos(True)
try:
    while True:

        main.scan.scan_cycle(resolution=8, lte_duration=7)
        #main.scan.plot_scan()
        threading.Thread(target=main.scan.plot_scan).start()
        # tmp = sorted(main.scan.scanres.keys())
        # for key in tmp:
        #     log("{} - {}".format(main.scan.scanres[key], key), 9)
        # log("\n")
except KeyboardInterrupt:
    main.ardu.run_trigger = False
    main.scan.run_trigger = False

log(main.scan.scanres, 9)
tmp = sorted(main.scan.scanres.keys())
for key in tmp:
    log("{} - {}".format(main.scan.scanres[key], key), 9)

