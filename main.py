from config import lte_stick_addi_1 as modem1
from fnc.huawei_com import LTEStick
from fnc.ardu_com import ArduCom
from fnc.scan_fnc import ScanSignals
import time


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

main.scan.run_scan_thread(2)
for i in range(130):
    # print("wait")
    time.sleep(1)

main.ardu.run_trigger = False
main.scan.run_trigger = False
