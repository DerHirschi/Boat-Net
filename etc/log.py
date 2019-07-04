#
# some Outputs for developing and debuging
#
from etc.var import get_time, date2filename

## Default Configs ##
class logDefaultConf(object):
    log_flag        = '> '          # Flag am Anfang der Ausgabe
    print_out       = True          # Ausgabe via print in console
    file_out        = False          # Ausgabe via Dateiausgabe

    print_ts        = True          # Timestamp in Printausgabe
    print_ts_opt    = 'time'        # Timestamp Optionen 'time'/'date'/'all'
    file_ts         = True          # Timestamp in Dateiausgabe
    file_ts_opt     = 'time'        # Timestamp Optionen 'time'/'date'/'all'

    log_path        = ''            # Pfad f Dateiausgabe '' > Projekt Rootverzeichniss
    log_filename    = 'bot.log'     # Dateiname
    filename_w_date = True          # Datum im Dateinamen (debug.log > debug_2017_9_5.log)

    class varHintConf():            # Config f Variablen detail Ausgabe #TODO Conf auch aus anderen Classes
        print_out   = True          # Timestamp in Printausgabe
        file_out    = False         # Timestamp in Dateiausgabe
        split_array = True          # Arrays, Listen & Tuple detailliert ausgeben (var_hint())
        # Message Frame
        frame_li = '**************************************************'
        frame_H  = '----------------- VAR DETAILS --------------------'
        frame_V  = '{} :--> {} '
        frame_T  = 'Type:-> {} '
        frame_S  = 'Size:-> {} '
        frame_AH = '------------------ FOR_EACH ----------------------'
        frame_AV = 'VAR {}: {} '
        frame_AT = 'TYPE : {} '
        frame_F  = '-------------- VAR DETAILS - ENDE ----------------'

class ERRORlogDefaultConf(logDefaultConf):
    log_flag        = '>< !! ERROR !! > '
    print_out       = True          # Ausgabe via print in console
    file_out        = True          # Ausgabe via Dateiausgabe
    #log_path        = ''            # Pfad f Dateiausgabe '' > Projekt Rootverzeichniss
    #log_filename    = 'debug.log'   # Dateiname
    #filename_w_date = True          # Datum im Dateinamen (debug.log > debug_2017_9_5.log)

class DEBUGlogConf(logDefaultConf):
    log_flag        = '>< ?? DEBUG ?? > '
    print_out       = True          # Ausgabe via print in console
    file_out        = True          # Ausgabe via Dateiausgabe
    log_path        = ''            # Pfad f Dateiausgabe '' > Projekt Rootverzeichniss
    log_filename    = 'debug.log'   # Dateiname
    filename_w_date = False         # Datum im Dateinamen (debug.log > debug_2017_9_5.log)

class FileERRlogConf(logDefaultConf):
    log_flag        = '>< Cant open File > : '
    print_out       = True          # Ausgabe via print in console
    file_out        = True          # Ausgabe via Dateiausgabe
    log_path        = ''            # Pfad f Dateiausgabe '' > Projekt Rootverzeichniss
    #log_filename    = 'debug.log'   # Dateiname
    #filename_w_date = False         # Datum im Dateinamen (debug.log > debug_2017_9_5.log)

# log mit verschiedenen Optionen & Ausgabeorten ( f z.B verschiedene Module )
# 0 = Default Log Ausgabe... Einstellungen siehe oben
# 1 = Default ERRORLog Ausgabe... Einstellungen siehe oben
# 2 = Default Filesys Error Ausgabe... Einstellungen siehe oben
# 9 = DEBUGLog Ausgabe... Einstellungen siehe oben
def log(data, opt=0):
    try:
        _opt = {
            1: ERRORlogDefaultConf,
            2: FileERRlogConf,
            9: DEBUGlogConf
        }[opt]
        if _opt.print_out or _opt.file_out:
            out(data, _opt.print_out, _opt.file_out, _opt)
    except:
        if logDefaultConf.print_out or logDefaultConf.file_out:
            out(data, logDefaultConf.print_out, logDefaultConf.file_out, logDefaultConf)


# Schnell Standardausgabe
# 1 Variable
# 2 Print   Ausgabe (opt) - ansonsten default Einstellunegn oben
# 3 Logfile Ausgabe (opt) - ansonsten default Einstellunegn oben
def out(data, p_out=logDefaultConf.print_out, f_out=logDefaultConf.file_out,
        conf_obj=logDefaultConf):

    def _mk_st(dat, trig, ts_op):
        if trig:
            return '[{}]{}'.format(get_time(ts_op, True), conf_obj.log_flag) + str(dat)
        else:
            return conf_obj.log_flag + str(dat)

    if p_out and type(data) == list or type(data) == tuple:
        for i in range(len(data)):
            print (_mk_st(data[i], conf_obj.print_ts, conf_obj.print_ts_opt))
    elif p_out:
        print (_mk_st(data, conf_obj.print_ts, conf_obj.print_ts_opt))
    if f_out:
        if conf_obj.filename_w_date:
            _f_n = conf_obj.log_path + date2filename(conf_obj.log_filename)
        else:
            _f_n = conf_obj.log_path + conf_obj.log_filename
        try:
            f = open(_f_n, 'a')
            if type(data) == list or type(data) == tuple:
                for i in range(len(data)):
                    f.write(_mk_st(data[i], conf_obj.file_ts, conf_obj.file_ts_opt) + '\n')
            else:
                f.write(_mk_st(data, conf_obj.file_ts, conf_obj.file_ts_opt) + '\n')
            f.close()
        except:
            print ('ERROR Log System log.py out().. Cant open Logfile.. Endlessloop')


# Variablen Details
# 1 Titel oder Beschreibung
# 2 Variable
# 3 Wenn Array oder Tuple, detailiert anzeigen (opt) ansonsten default Einstellunegn oben
# 4 Print   Ausgabe (opt) - ansonsten default Einstellunegn oben
# 5 Logfile Ausgabe (opt) - ansonsten default Einstellunegn oben
def var_hint(title, output,
             spl_array=logDefaultConf.varHintConf.split_array,
             p_out=logDefaultConf.varHintConf.print_out,
             f_out=logDefaultConf.varHintConf.file_out,
             confobj=logDefaultConf
             ):
    # Message Frame
    _fr  = confobj.varHintConf
    _tem = [
               '',
               _fr.frame_li,
               _fr.frame_H,
               _fr.frame_V.format(title, str(output)),
               _fr.frame_T.format(type(output))
           ]

    if type(output) != int:
        try:
            _tem.append(_fr.frame_S.format(len(output)))
        except:
            pass

    if (type(output) == tuple or type(output) == list) and spl_array:
        _tem.append(_fr.frame_AH)
        for i in range(len(output)):
            _tem = _tem + ['', _fr.frame_AV.format(i, str(output[i])), _fr.frame_AT.format(type(output[i]))]
            try:
                _tem.append(_fr.frame_S.format(len(output[i]) ))
            except:
                pass
    _tem = _tem + [_fr.frame_F, _fr.frame_li, '']

    for i in range(len(_tem)):
        out(_tem[i], p_out, f_out)

# Test it !!!
if __name__ == '__main__':
    log('test {}'.format(54455645))
    log('test {}'.format(54455645), 1)
    log('test {}'.format(54455645), 2)
    log(['test1','test2',3], 2)
    out(['this', 'is', 'a', 'test'])
    out(2)
    out('string')

    var_hint('TESTTESTTTT', 5235234)
    var_hint('TESTTESTTTT', ['test', 325, (333, 335), True, 'sfga'])
    var_hint('TESTTESTTTT', ['test', 325, (333, 335), 'sfga'], True)
    var_hint('TESTTESTTTT', ['test', 325, (333, 335), 325, (333, 335), 325, (333, 335), 'sfga'], True)
    var_hint('TESTTESTTTT', ['test', 325, (333, 335), 'sfga', 325, (333, 335), 'sfga'], True)
    var_hint('TESTTESTTTT', ['test', 325, (333, 335), 'sfga', 325, (333, 335), 'sfga'], True, True, True)
    var_hint('TESTTESTTTT', ['test', 325, (333, 335), 'sfga', 325, (333, 335), 'sfga'], False, True, True)
    var_hint('TESTTESTTTT', ['test', 325, (333, 335), 'sfga', 325, (333, 335), 'sfga'], False)

