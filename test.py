from config import lte_stick_addi_1 as modem1
from main import Main
from etc.log import log
from etc.var import list_parts
import time
import threading


main = Main(modem1)
if main.run_trigger:
    print("Main init")
    # main.ardu.set_servo(val=200)
    main.ardu.set_gimbal_lock_hdg() # TODO gimbal_lock_hdg has to set back to arduino after reinit
    main.ardu.set_servo(_val=512, _speed=200, wait_servo_confirm=True)

    time.sleep(1)
    main.ardu.toggle_servos(True)
    main.ardu.set_servo(_val=1000, _speed=150, wait_servo_confirm=True)
    try:
        print(main.ardu.acc_roll_cal)
        print(main.ardu.acc_pitch_cal)
        main.ardu.get_acc_cal_parm()

        while main.run_trigger:
            time.sleep(1)

    except KeyboardInterrupt:
        print(main.ardu.acc_roll_cal)
        print(main.ardu.acc_pitch_cal)
        print("Wird beendet ... ")
        main.ardu.set_servo(_val=512, _speed=150, new_gimbal_lock=True)
        time.sleep(2)
        main.run_trigger = False



    # main.ardu.set_servo(val=512, speed=150)
    # time.sleep(2)
    # main.run_trigger = False
    # log(main.scan.scanres, 9)
    # tmp = sorted(main.scan.scanres.keys())
    # for key in tmp:
    #     log("{} - {}".format(main.scan.scanres[key], key), 9)

else:
    print("Main init failed. . .")
