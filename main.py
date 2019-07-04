from config import lte_stick_addi_1 as modem1
from fnc.huawei import LTEStick


lte_1 = LTEStick(modem1)
for i in range(10):
    print(LTEStick.get_string(lte_1))

