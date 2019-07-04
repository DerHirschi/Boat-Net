from config import lte_stick_addi
from fnc.huawei import LTEStick


lte_stick_1 = LTEStick(lte_stick_addi)
for i in range(10):
    print(LTEStick.get_string(lte_stick_1))

