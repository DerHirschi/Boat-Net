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

        # while main.run_trigger:
        if main.ardu.run_trigger:
            main.scan.scan_one_cycle(_resolution=40, _lte_duration=5, _speed=150)
            try:
                # main.scan.scan_cycle(_resolution=32, _lte_duration=5, _duration=1, _net_mode=0)

                print("")
            except ConnectionError:
            # while True:
            #     print(main.lte.get_string())
                print("Wird beendet ... Connection Error LTE")
                main.ardu.set_servo(_val=512, _speed=200, new_gimbal_lock=True)
                time.sleep(2)
                main.run_trigger = False
            # main.scan.get_signal_peak_in_range(main.scan.scanres3G, -10)
            # main.scan.get_signal_peak_in_range(main.scan.scanres4G, -6)
            _n = []
            _i = 0
            for _in in range(200):
                _n.append(_i)
                _i += 1
            _i = 500
            for _in in range(300):
                _n.append(_i)
                _i += 1

            # main.scan.scan_hdg_range(_n, 2, _servo_speed=100)
            log("", 9)
            log("len scanres3G arrays " + str(len(list_parts(sorted(main.scan.scanres3G.keys())))), 9)
            log("", 9)
            log("scanres3G arrays " + str(list_parts(sorted(main.scan.scanres3G.keys()))), 9)

            log("", 9)

            _n = []
            _i = 700
            for _in in range(300):
                _n.append(_i)
                _i += 1
            # main.scan.scan_hdg_range(_n, 3, _servo_speed=100)
            log("", 9)
            log("", 9)
            log("", 9)
            main.scan.get_visible_hdg()
            log("", 9)
            log("", 9)
            log("", 9)
            # log("scanres3G keys  > " + str(sorted(main.scan.scanres3G.keys())), 9)
            # log("", 9)
            # log("", 9)
            # log("scanres4G keys  > " + str(sorted(main.scan.scanres4G.keys())), 9)
            log("", 9)
            log("", 9)
            log("", 9)
            log("", 9)
            # log("sig_array_3G keys  > " + str(sorted(main.scan.cells_3G.keys())), 9)
            log("", 9)
            # log("sig_array_4G keys  > " + str(sorted(main.scan.cells_4G.keys())), 9)
            log("", 9)
            log("", 9)
            log("", 9)
            # log("get_not_scanned_hdg 2 > " + str(main.scan.get_not_scanned_vis_hdg(2)), 9)
            log("", 9)
            # log("get_not_scanned_hdg 3 > " + str(main.scan.get_not_scanned_vis_hdg(3)), 9)
            log("", 9)
            log("", 9)

            # main.scan.get_signal_arrays(2)    # called in scan.scan_cycle() after scan.scan_full_range()
            # TODO sig_array_3G & sig_array_4G fill gaps between cells(arrays)
            # log("get_best_cell_hdg 1" + str(main.scan.get_best_cell_hdg(_mode=1)), 9)
            # log("get_best_cell_hdg 2" + str(main.scan.get_best_cell_hdg(_mode=2)), 9)
            # log("get_best_cell_hdg 3" + str(main.scan.get_best_cell_hdg(_mode=3)), 9)
            threading.Thread(target=main.ardu.set_servo, args=(1, 512, 500, False, True)).start()
            log("Plot Signals 2", 9)
            main.web.plot_lte_signals(2)
            time.sleep(1)
            log("Plot Signals 3", 9)
            main.web.plot_lte_signals(3)
            # FIXME
            # time.sleep(1)
            # log("Plot Arrays 2", 9)
            # main.web.plot_signal_arrays(2)
            # time.sleep(1)
            # log("Plot Arrays 3", 9)
            # main.web.plot_signal_arrays(3)
            # FIXME END
            log("", 9)
            tmp = sorted(main.scan.scanres3G.keys())
            for key in tmp:
                log("scanres3G - {} - {}".format(main.scan.scanres3G[key], key), 9)
            log("", 9)
            tmp = sorted(main.scan.scanres4G.keys())
            for key in tmp:
                log("scanres4G - {} - {}".format(main.scan.scanres4G[key], key), 9)

            main.scan.get_plmn_list()
            print("")
            print(main.scan.plmn_list)
            main.web.write_plmn_list2web()
            main.ardu.set_servo(_val=512, _speed=150, new_gimbal_lock=True)
            print("")
            print("Wird beendet ... ")
            time.sleep(2)
            main.run_trigger = False
    except KeyboardInterrupt:
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
