from fnc.huawei import LTEStick


lte_stick_1 = LTEStick()
for i in range(10):
    print(LTEStick.get_string(lte_stick_1))

