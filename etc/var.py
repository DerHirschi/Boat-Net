import os
import time


def array2string(data, cut_flag=',', cut_last=True):
    _temp = ''
    for i in range(len(data)):
        if type(data[i]) != str:
            _temp = _temp + str(data[i]) + cut_flag
        else:
            _temp = _temp + data[i] + cut_flag
    if cut_last:
        return _temp[:(len(_temp) - 1)]
    else:
        return _temp[:(len(_temp))]


def string2array(data, cut_flag=' ', cut_blank=True, conv2int=True):
    _data = data.split(cut_flag)
    _temp = []
    for i in range(len(_data)):
        if _data[i] == '' and cut_blank:
            pass
        else:
            try:
                if conv2int:
                    _temp = _temp + [int(_data[i])]
                else:
                    _temp = _temp + [_data[i]]
            except:
                _temp = _temp + [_data[i]]
    return _temp


# Quelle: https://stackoverflow.com/questions/931092/reverse-a-string-in-python
def rev_str(a_string):
    return a_string[::-1]


def ck_str(_data):
    if type(_data) != str:
        _data = str(_data)
    return _data


def ck_list_ele_type(_data, _type):
    if not type(_data) == list:
        return 0
    else:
        for _i in _data:
            if type(_i) != _type:
                return 0
        return 1


def get_time(opt='all', string=False):
    def _monat(lst, trig):
        if not trig:
            return lst
        else:
            return {
                'Jan': 1,
                'Feb': 2,
                'Mar': 3,
                'Apr': 4,
                'May': 5,
                'Jun': 6,
                'Jul': 7,
                'Aug': 8,
                'Sep': 9,
                'Oct': 10,
                'Nov': 11,
                'Dec': 12,
            }[lst]

    def _conv_all():
        if string:
            return array2string(string2array(time.ctime(), ' '), '-')
        else:
            return string2array(time.ctime(), ' ')

    _day_string = {
        True: 0,
        False: 2,
    }

    return {
        # 'all': string2array(time.ctime(), ' '),
        'all': _conv_all(),
        'year': string2array(time.ctime(), ' ', True, not string)[4],
        'mon': _monat(string2array(time.ctime(), ' ')[1], not string),
        'day': string2array(time.ctime(), ' ')[_day_string[string]],
        'time': string2array(time.ctime(), ' ')[3],
        'h': string2array(str(string2array(time.ctime(), ' ')[3]), ':', True, not string)[0],
        'min': string2array(str(string2array(time.ctime(), ' ')[3]), ':', True, not string)[1],
        'sek': string2array(str(string2array(time.ctime(), ' ')[3]), ':', True, not string)[2],
    }[opt]


# Fuegt an Dateinamenstring Datum oder Zeit an
# 1 Dateiname
# 2 Option ('date'/'time')
# 3 Cut Flag -> c_f='_' -> 2017_9_1 or c_f='!' -> 2017!9!1
# !!!! Prueft nicht ob Datei schon existiert !!!! fuer log Funktion

def date2filename(f_name, time_form='date', cut_flag='_'):
    _i = f_name.find('.')
    _temp = f_name[_i:]
    return f_name[:_i] + '_' + build_date_st(time_form, cut_flag) + _temp

# 1 Option 'date'/'time'/'all'
# 2 Cut_Flag -> c_f='_' -> 2017_9_1 or c_f='!' -> 2017!9!1


def build_date_st(t_f, c_f):
    if t_f == 'all':
        return build_date_st('date', c_f) + c_f + build_date_st('time', c_f)
    else:
        return {
            'date': str(get_time('year')) + c_f + str(get_time('mon')) + c_f + str(get_time('day')),
            'time': str(get_time('h')) + c_f + str(get_time('min')) + c_f + str(get_time('sek')),
        }[t_f]

# Prueft ob Datei schon existiert.
# Wenn ja wird ein count (_1 / _2 ...) an den Dateinamen angehaengt
# und der neue Dateinnamen String zurueck gegeben
# 1 Dateiname
# 2 Option ( 'count'/'date'/'time' ) -> date & time fuegt Datum oder Zeit vor dem Count ein


def count_filename(f_name, opt='count'):
    def _count_st(_f_name, _end):
        if not os.path.exists(_f_name + _end):
            return _f_name + _end
        else:
            _n = 1
            _l = len(_f_name)
            while os.path.exists(_f_name + _end):
                _f_name = _f_name[:_l] + '_{}'.format(_n)
                _n += 1
            return _f_name + _end

    _i = (f_name.find('.'))
    _e = f_name[_i:]
    _n = f_name[:_i]

    if opt == 'count':
        return _count_st(_n, _e)
    else:
        return {
            'date': _count_st(_n + build_date_st(opt, '-'), _e),
            'time': _count_st(_n + build_date_st(opt, '-'), _e)
        }[opt]


# Andert Dateiendung
def change_file_ext(f_name, ext):
    return f_name[:(f_name.find('.'))] + '.{}'.format(ext)


# Overflow a int var
def overflow_int(_var, _bit=8):
    _bit = (2**_bit) - 1
    if _var > _bit:
        return (_var - _bit), True
    else:
        return _var, False


def overflow_value(val, overflow=1024):
    return val % overflow


def map_val(sensor_val, in_min, in_max, out_min, out_max):
    # https://stackoverflow.com/questions/1969240/mapping-a-range-of-values-to-another
    out_range = out_max - out_min
    in_range = in_max - in_min
    in_val = sensor_val - in_min
    val = (float(in_val)/in_range)*out_range
    out_val = out_min + val
    return out_val



if __name__ == '__main__':
    print(overflow_int(256))
