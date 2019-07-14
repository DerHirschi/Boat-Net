import time
import threading
from etc.var import overflow_value, list_avg, map_val
from etc.log import log


class ScanSignals:
    def __init__(self, _lte_stick, _ardu):
        self.lte_stick = _lte_stick
        self.arduino = _ardu
        self.scanres3G = {}
        self.scanres4G = {}
        self.sig_array_3G = {}
        self.sig_array_4G = {}
        self.threshold_3G = -15
        self.threshold_4G = -15
        self.plmn_list = []
        self.null_hdg = self.arduino.heading    # Flag has to set if delete self.scanres
        self.run_trigger = False                # Loop stopper
        # Plot Init #
        self.val_range = 1023
        self.N = int(self.val_range / (self.arduino.servo_max_angle - self.arduino.servo_min_angle) * 360)

    def get_scanres_dict(self, _net_mode):
        return {
            2: self.scanres3G,
            3: self.scanres4G,
            7: self.scanres4G       # needed in get_lte_signals_avg()
        }[_net_mode]

    def get_threshold(self, _net_mode):
        return {
            2: self.threshold_3G,
            3: self.threshold_4G
        }[_net_mode]

    def get_sig_array_dict(self, _net_mode):
        return {
            2: self.sig_array_3G,
            3: self.sig_array_4G,
        }[_net_mode]

    def set_sig_array_dict(self, _res, _net_mode):
        if _net_mode == 2:
            self.sig_array_3G = _res
        elif _net_mode == 3:
            self.sig_array_4G = _res

    def get_plmn_list(self):
        _plmn_list = self.lte_stick.get_plmn_list()
        _res = []
        for _net in _plmn_list:
            _res.append(_net['FullName'])
        self.plmn_list = _res

    def get_lte_signals_avg(self, _hdg, _resolution, _duration=5):
        _temp_sig = [0, 0, 0, 0]
        for _n in range(_duration):       # Get average of scan values
            _sigs = self.lte_stick.get_string()
            if _sigs:
                if None not in _sigs:
                    _temp_sig = [_temp_sig[0] + _sigs[0], _temp_sig[1] + _sigs[1], _temp_sig[2] + _sigs[2], _sigs[3]]
                else:
                    if _sigs[3]:
                        _temp_sig[3] = _sigs[3]

        if _temp_sig[3] in [2, 7]:
            if None not in _temp_sig:
                _range_begin = int(_resolution / 2)
                _temp_res = self.get_scanres_dict(_temp_sig[3])

                for z in range(_resolution - 1):
                    _i = (_hdg - _range_begin + z)
                    _i = overflow_value(_i, self.N)
                    if _i in _temp_res:       # Calculate average for each founded value
                        for _ind in range(3):
                            _temp_res[_i][_ind] = round(((_temp_res[_i][_ind] + (_temp_sig[_ind] / _duration)) / 2), 2)
                    else:
                        _temp_res[_i] = [round((_temp_sig[0] / _duration), 2),
                                         round((_temp_sig[1] / _duration), 2),
                                         round((_temp_sig[2] / _duration), 2)]
            else:
                _temp_res = [None, None, None, _temp_sig[3]]

            if _temp_sig[3] == 2:
                self.scanres3G = _temp_res
            elif _temp_sig[3] == 7:
                self.scanres4G = _temp_res

    def get_hdg_diff_mapped(self):
        _hdg = self.arduino.heading - self.arduino.lock_hdg
        return int(map_val(_hdg, -360, 360, -self.N, self.N))

    def set_servo_hdg(self, val):
        self.arduino.set_servo(servo=1, _val=val)

    def scan_full_range(self, _resolution=24, _loop=None, _duration=5):
        _val = 0
        _n = 0
        _n_max = self.val_range
        _step = int(_n_max / (_resolution + 1))
        _n_high = -self.get_hdg_diff_mapped() + _n_max  # if loop:
        _n_low = self.get_hdg_diff_mapped()            # if not loop:
        while _n <= self.N and self.run_trigger:
            if _loop:
                _dif = self.get_hdg_diff_mapped() + _n_max
                _val = _n_high - _n
                if (_n + _n_low) >= _dif:
                    break
            else:
                _dif = _n_max - self.get_hdg_diff_mapped()
                _val = -_n_low + _n
                if (-_n_low + _n) >= _dif:
                    break
            self.set_servo_hdg(_val)
            time.sleep(0.1)
            self.get_lte_signals_avg(_duration=_duration, _hdg=_val, _resolution=_resolution)
            _n += _step

    def scan_cycle(self, _duration=2, _timer=-1, _resolution=32, _lte_duration=7, _net_mode=0):
        # net_mode 0: scant 3G u 4G
        log("Run Scan Thread", 9)
        _lo = True
        _z = 0
        _net_mode_switch = False
        if _net_mode == 0:
            _net_mode_switch = True
            _net_mode = 2
            _duration = _duration * 2

        self.lte_stick.set_net_mode(_net_mode)

        self.run_trigger = True
        if _timer != -1:
            ti = time.time()
            while self.run_trigger and self.arduino.run_trigger:
                print("Timed Thread")
                self.scan_full_range(_resolution=_resolution, _loop=_lo, _duration=_lte_duration)
                self.get_signal_arrays(_net_mode)                           # Calculate Signal Arrays
                if _lo:
                    _lo = False
                else:
                    _z += 1
                    _lo = True

                if _net_mode_switch and _z == 1:
                    _z = 0
                    if _net_mode == 2:
                        _net_mode = 3
                    elif _net_mode == 3:
                        _net_mode = 2
                    try:
                        self.lte_stick.set_net_mode(_net_mode)
                    except ConnectionError:
                        self.run_trigger = False
                        raise
                if (time.time() - ti) > _timer:
                    break
        else:

            for n in range(_duration):
                if not self.run_trigger or not self.arduino.run_trigger:
                    break
                log("Scan Nr: " + str(n), 9)
                self.scan_full_range(_resolution=_resolution, _loop=_lo)
                self.get_signal_arrays(_net_mode)                           # Calculate Signal Arrays
                if _lo:
                    _lo = False
                else:
                    _lo = True
                    _z += 1

                if _net_mode_switch and _z == 1 and (_duration - 1) != n:
                    _z = 0
                    if _net_mode == 2:
                        _net_mode = 3
                    elif _net_mode == 3:
                        _net_mode = 2
                    log("Switch Band " + str(_net_mode), 9)
                    try:
                        self.lte_stick.set_net_mode(_net_mode)
                    except ConnectionError:
                        raise
        self.run_trigger = False

    def run_scan_cycle_thread(self, duration=2, timer=-1, resolution=32, lte_duration=7):
        if self.arduino.run_trigger:
            return threading.Thread(target=self.scan_cycle, args=(duration, timer, resolution, lte_duration)).start()
        else:
            return False

    def get_best_cell_hdg(self, _mode=1):
        # _mode 1 = best Cell 3G/4G
        # _mode 2 = best Cell 3G
        # _mode 3 = best Cell 4G
        _cells = {
            1: self.sig_array_3G,
            2: self.sig_array_3G,
            3: self.sig_array_4G
        }[_mode]
        _cell_keys = sorted(_cells.keys(), reverse=True)

        if _mode == 1:
            _flag = self.sig_array_4G
            _flag_keys = sorted(_flag.keys(), reverse=True)
            if _cell_keys and _flag_keys:
                if _flag_keys[0] > _cell_keys[0]:
                    _mode = 3
                    _cells = _flag
                    _cell_keys = _flag_keys
            elif not _cell_keys and not _flag_keys:
                return None
            elif not _cell_keys:
                _cells = _flag
                _cell_keys = _flag_keys
        elif _mode == 2 and not _cell_keys:
            return None
        elif _mode == 3 and not _cell_keys:
            return None
        _scan_arr = _cells[_cell_keys[0]]
        # log("_cell_keys " + str(_cell_keys), 9)
        _mode = max(_mode, 2)
        return self.get_peak_from_hgd_list(_scan_arr, _mode), _mode     # (signal, hdg), NetMode

    @staticmethod
    def get_peak(_scanres):
        _res, _key = None, None
        for _i in _scanres.keys():
            if _res:
                _temp = _scanres[_i]
                if _temp[0] > _res[0]:
                    _res, _key = _temp, _i
            else:
                _res, _key = _scanres[_i], _i
        return _res, _key

    def get_peak_from_hgd_list(self, _hdg_list, _net_mode):
        _scanres = self.get_scanres_dict(_net_mode)
        _res = -100, 0
        for _hdg in _hdg_list:
            _flag = _scanres[_hdg][0], _hdg
            if _flag[0] > _res[0]:
                _res = _flag
        return _res                                         # signal, hdg_key

    def get_signal_arrays(self, _net_mode, _threshold=-15):
        # TODO call this() after complete scan cycle or after one shot scan ( extra fnc for onh shot )
        # signal threshold: 4G/RSRQ  = -15
        # signal threshold: 3G/EC/IO = -15
        _scanres = self.get_scanres_dict(_net_mode)
        _temp_res = {}
        _temp_arrays = []
        _threshold = self.get_threshold(_net_mode)
        for _key in _scanres.keys():                # Drop all values below lowest signal
            if _scanres[_key][0] >= _threshold:
                _temp_res[_key] = _scanres[_key][0]

        _temp_keys = sorted(_temp_res.keys())
        if _temp_keys:                             # Check if some values available after dropping under threshold values
            _i = 0
            _flag_key = _temp_keys[_i]
            _n = 0
            _n_key = 0
            while _n_key != len(_temp_keys):            # put every range(array) in an array..
                if _flag_key == _n:                     # if value is in range
                    if len(_temp_arrays) == _i:         # if new range
                        _temp_arrays.append([_n])
                    else:                               # if range exist push next value to array
                        _temp_arrays[_i].append(_n)
                    _n_key += 1
                    if _n_key < len(_temp_keys):        # Break if all keys are irritated
                        _flag_key = _temp_keys[_n_key]  # pull nex key to temp
                    else:
                        break
                else:                                   # if value not in range
                    _i = len(_temp_arrays)              # next range
                _n += 1

            _avg_res = {}                               # Return value dict
            for _ra in _temp_arrays:                    # Calculate average for each range
                _temp = []
                for _ke in _ra:
                    _temp.append(_scanres[_ke][0])

                _array_weight = round((abs(_threshold) - list_avg(_temp)) * len(_temp))
                _avg_res[_array_weight] = _ra
            # log("", 9)
            # log("_avg_res  " + str(_avg_res), 9)
            self.set_sig_array_dict(_avg_res, _net_mode)  # set dict. Keys = weight, value = list of servo hdg for range
        else:
            self.set_sig_array_dict({}, _net_mode)  # or {} if no keys in scanres because all sig vals under threshold
            # I start to love Pythons dictionaries
