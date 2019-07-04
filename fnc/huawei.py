from huawei_lte_api.Client import Client
from huawei_lte_api.AuthorizedConnection import AuthorizedConnection
from huawei_lte_api.exceptions import ResponseErrorLoginCsfrException


class LTEStick():
    def __init__(self):
        self.client = None
        self.rsrq = -999
        self.sinr = -999
        self.rsrp = -999
        try:
            self.client = Client(AuthorizedConnection('http://192.168.8.1/'))
        except ResponseErrorLoginCsfrException:
            print("Connection2Modem Error ...")
            raise

    def get_int(self, value):
        if(value is None):
            return None
        elif(value == "Unknown"):
            return None
        else:
            return int(value.split('d')[0])

    def get_string(self):
        signal_info = self.client.device.signal()
        mode = self.get_int(signal_info["mode"])
        # lte_quality_signal_dict = { //4G
        #                   'rsrp': (-80, -90, -100),
        #                   'rsrq': (-10, -15, -20),
        #                   'sinr': (20, 13, 0),
        #                  }
        if (mode == 7):  # 4G
            self.rsrq = self.get_int(signal_info["rsrq"])
            self.rsrp = self.get_int(signal_info["rsrp"])
            self.sinr = self.get_int(signal_info["sinr"])
        elif (mode == 2):  # 3G
            self.rsrq = self.get_int(signal_info["ecio"])
            self.sinr = self.get_int(signal_info["rssi"])
            self.rsrp = self.get_int(signal_info["rscp"])
        else:
            self.rsrq = -999
            self.sinr = -999
            self.rsrp = -999

        return self.rsrq, self.rsrp, self.sinr, mode
