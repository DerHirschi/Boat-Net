import time
from huawei_lte_api.Client import Client
from huawei_lte_api.AuthorizedConnection import AuthorizedConnection
from huawei_lte_api.exceptions import ResponseErrorException


class LTEStick:
    def __init__(self, stick_addi):
        self.client = None
        self.rsrq = -999
        self.sinr = -999
        self.rsrp = -999
        try:
            self.client = Client(AuthorizedConnection(stick_addi))
        except Exception:
            print("Connection2Modem Error ...")
            raise ConnectionError

    def get_int(self, value):
        if value is None:
            return None
        elif value == "Unknown":
            return None
        else:
            return int(value.split('d')[0])

    def get_string(self, trys=2, sleep=0.5):
        mode = None
        for e in range(trys):
            signal_info = self.client.device.signal()
            mode = self.get_int(signal_info["mode"])
            # lte_quality_signal_dict = { //4G
            #                   'rsrp': (-80, -90, -100),
            #                   'rsrq': (-10, -15, -20),
            #                   'sinr': (20, 13, 0),
            #                  }
            if mode == 7:  # 4G
                self.rsrq = self.get_int(signal_info["rsrq"])
                self.rsrp = self.get_int(signal_info["rsrp"])
                self.sinr = self.get_int(signal_info["sinr"])
            elif mode == 2:  # 3G
                self.rsrq = self.get_int(signal_info["ecio"])
                self.sinr = self.get_int(signal_info["rssi"])
                self.rsrp = self.get_int(signal_info["rscp"])
            else:
                self.rsrq = None
                self.sinr = None
                self.rsrp = None
                mode = None
            if None not in (self.rsrq, self.rsrp, self.sinr, mode):
                return self.rsrq, self.rsrp, self.sinr, mode
            else:
                time.sleep(sleep)
        if mode:
            return None, None, None, mode
        else:
            return None

    def reboot(self):
        try:        # for E 3372
            self.client.device.reboot()
        except ResponseErrorException:
            print('Rebooting LTE-Modem ...')
            time.sleep(20)
            return True
        except Exception:
            raise ConnectionError
        return False

    def get_net_mode(self):
        return self.client.net.net_mode()

    def get_net_mode_list(self):
        return self.client.net.net_mode_list()

    def get_plmn_list(self):
        return self.client.net.plmn_list()['Networks']['Network']

    def set_net_mode(self, net_mode=4):
        # net_mode
        # 0 = auto
        # 1 = 2G
        # 2 = 3G
        # 3 = 4G
        # 4 = best available mode
        mode_list = self.get_net_mode_list()
        available_modes = mode_list['AccessList']['Access']
        if '02' in available_modes or '03' in available_modes or net_mode == 0:
            lte_band = mode_list['LTEBandList']['LTEBand'][0]['Value']
            net_band = mode_list['LTEBandList']['LTEBand'][1]['Value']
            if net_mode == 4:
                net_mode = available_modes[-1:]

            net_mode = '0' + str(net_mode)
            try:    # E 3372
                self.client.net.set_net_mode(networkmode=net_mode, networkband=net_band, lteband=lte_band)
            except ResponseErrorException:
                e_c = 0
                while self.client.device.signal()['mode'] is None:
                    if e_c > 10:
                        print("Error.. None Net Mode after changing Net Mode .. No NET ??")
                        # raise ConnectionError
                        break
                    time.sleep(1)
                    e_c += 1

                # print("New Net-Mode set: " + str(net_mode))
                return net_mode
            except Exception:
                print("Error.. while trying to set Net Mode ..")
                raise ConnectionError
            return False
        else:
            return False
