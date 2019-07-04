# Author DerHirschi
import os

from etc.var import count_filename, change_file_ext
from etc.log import log
from etc.crypt import enc, dec


# 1 Daten ( egal welcher daten typ)
# 2 Dateiname
# 3 (opt)Neue Datei erstell wenn Datei schon existiert - default True
# 4 (opt)Pfad - default Projekt Rootverzeichniss
# 5 (opt)Option Datum oder Zeit im Dateinamen + Count
#   'count'/'date'/'time'
# return filename string -> return '' if except
def write(data, f_ile, new_file=True, path='', opt='count'):
    def _add_nl(st_r):
        if type(st_r) != str:
            st_r = str(st_r)
        if bool(st_r.find('\n') + 1):
            return st_r
        else:
            return st_r + '\n'

    _f_name = path + f_ile
    if new_file:
        _f_name = count_filename(_f_name, opt)

    try:
        _f = open(_f_name, 'a')

        if type(data) == str:
            _f.write(_add_nl(data))
        elif type(data) == list or type(data) == tuple:
            for i in range(len(data)):
                _f.write(_add_nl(data[i]))
        elif type(data) != dict:
            _f.write(_add_nl(data))

        _f.close()
        return _f_name
    except:
        log('{} - write() Writefile'.format(_f_name), 2)
        return ''


def try_file(f_name, opt):
    try:
        return open(f_name, opt)
    except:
        log('{} - try_file() opt: {}'.format(f_name, opt), 2)
        return False


# 1 Path + Filename
# 2 Key (Password)
# 3 (opt) Output Filename extension.. examples: ('cry'/'no'/'zip' ..) - default *.enc
# 4 (opt) True = Insert IV in File
# return IV, Otuputfilename
def enc_file(f_ile, key, f_ext='enc', iv_add=True):
    _wf_name = count_filename(change_file_ext(f_ile, f_ext))
    if os.path.exists(f_ile) and not os.path.exists(_wf_name):
        _rf = try_file(f_ile, 'r')
        _wf = try_file(_wf_name, 'w')
        if _rf and _wf:
            _res = enc(key, _rf.read())
            _rf.close()
            if iv_add:
                _wf.write(_res[1] + _res[0])
            else:
                _wf.write(_res[0])
            _wf.close()
            return _res[1], _wf_name

# 1 Path + Filename
# 2 Key (Password)
# 3 (opt) Output Filename extension.. examples: ('cry'/'no'/'zip' ..) - default *.dec
# 4 (opt) IV .. if leave '' the fnc take the IV from File
# return Otuputfilename
def dec_file(f_ile, key, f_ext='dec', iv=''):
    _wf_name = count_filename(change_file_ext(f_ile, f_ext))
    if os.path.exists(f_ile) and not os.path.exists(_wf_name):
        _rf = try_file(f_ile, 'r')
        _wf = try_file(_wf_name, 'w')
        if _rf and _wf:
            _tmp = _rf.read()
            _rf.close()
            if iv == '':
                _wf.write(dec(key, _tmp[16:], _tmp[:16]))
            else:
                _wf.write(dec(key, _tmp, iv))

            _wf.close()
            return _wf_name
        else:
            return ''
    else:
        return ''


# Test it !!!

# enc_file('test.txt', 'asd4tgdhGFSdhkdsas34shWshAsh4')
# write('jeahhh','test.txt', True, '',)
# write('jeahhh','test.txt', True, '', 'date')
# write('jeahhh','test.txt', True, '', 'time')
# write('jeahhh','test.txt', True, '', 'time')
