from config import lte_stick_addi_1 as modem1
from fnc.huawei import LTEStick
from fnc.ardu_com import ArduCom
import time
ardu = None
try:
    ardu = ArduCom()
except:
    print("E2")


if(ardu):
    time.sleep(30)
    ardu.set_servo(1, 800)
    time.sleep(3)
    ardu.set_servo(1, 200, 150)
    time.sleep(3)
    ardu.toggle_servos(True)
    time.sleep(3)
    ardu.toggle_servos(False)
    time.sleep(3)
    ardu.toggle_servos(True)
    ardu.run_trigger = False
'''
try:
    lte_1 = LTEStick(modem1)
    for i in range(10):
        print(LTEStick.get_string(lte_1))
except Exception:
    print("E3")
'''
