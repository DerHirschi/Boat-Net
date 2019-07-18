import numpy as np
import matplotlib.cm as cm
import os
import shutil
import config
import time
from etc.var import overflow_value, change_file_ext, map_val
from etc.log import log
import matplotlib as mpl
from six.moves import cPickle as Pickle         # for performance

if not os.environ.get('DISPLAY'):     # Get an Error from python.tk.. Solution from:
    mpl.use('Agg')
import matplotlib.pyplot as plt


class Data2Web:
    def __init__(self):
        self.run_trigger = False
        # self.scan = scan_cl
        # HTML Location
        self.html_images = config.html_images
        self.N = 0
        self.val_range = 0
        if self.load_configs():
            self.run_trigger = True
            # Signal Plot
            self.theta = np.arange(0.0, 2 * np.pi, 2 * np.pi / self.N)
            self.center = int((self.N - self.val_range) / 2)
            self.radii = []
            self.radii_array = []
            self.width = np.pi / 4 * np.random.rand(self.N)
            _f = open(config.html_root + change_file_ext(config.html_lte_page, 'ba'), 'r')
            self.html_str_lte_page = _f.read()
            _f.close()
            for _i in range(self.N):
                self.radii.append(-1)                   # -1 to show unscanned array in plot
                self.radii_array.append(0)
            for _i in range(len(self.width)):
                self.width[_i] = 6 / self.N

    def load_configs(self):
        with open('web_gui/data/configs.pkl', 'rb') as f:
            _di = Pickle.load(f)
            if _di:
                self.N = _di['N']
                self.val_range = _di['val']
                return True
        return False

    def get_scanres_filename(self, _net_mode):
        return {
            2: 'web_gui/data/3g.pkl',
            3: 'web_gui/data/4g.pkl'
        }[_net_mode]

    def load_scanres(self, _net_mode):
        # Source: https://stackoverflow.com/questions/40219946/python-save-dictionaries-through-numpy-save
        _di = None
        _f_name = self.get_scanres_filename(_net_mode)
        with open(_f_name, 'rb') as f:
            _di = Pickle.load(f)
        if _di:
            return _di

    def load_cells(self, _net_mode):
        # Source: https://stackoverflow.com/questions/40219946/python-save-dictionaries-through-numpy-save
        _di = None
        _f_name = self.get_scanres_filename(_net_mode)
        with open(_f_name + '_c', 'rb') as f:
            _di = Pickle.load(f)
        if _di:
            return _di

    def write_plmn_list2web(self, get_new_plmn=False):
        plmn = None
        if get_new_plmn:
            with open('data/plm.pkl', 'rb') as f:
                plmn = Pickle.load(f)

        html_str = self.html_str_lte_page
        i = 0
        for st in ['dummy_netze1', 'dummy_netze2', 'dummy_netze3']:
            if i < len(plmn):
                html_str = html_str.replace(st, plmn[i])
            else:
                html_str = html_str.replace(st, '')
            i += 1
        f = open(config.html_root + config.html_lte_page, 'w')
        f.write(html_str)
        f.close()

    def plot_lte_signals(self, _net_mode=2, _signal_type=0, _plot_signal_array=True):
        # TODO Werte glaetten ( evtl )
        # TODO Performance !!!
        # TODO extra Plot for Signal Arrays
        # signal_type 1 = Plot Signal 'rsrq'
        # signal_type 2 = Plot Signal 'rsrp'
        # signal_type 3 = Plot Signal 'sinr'
        # signal_type 0 = Plot for all Signals
        # net_mode 2 = 3G
        # net_mode 3 = 4G

        def _get_mode_config(_mo, _n_mo):
            return {
                2: {    # Null_val, colorrange, filename, mode
                    1: (20., 10, '3gecio-800x800', (_mo - 1)),
                    2: (120., 60, '3grscp-800x800', (_mo - 1)),
                    3: (110., 40, '3grssi-800x800', (_mo - 1))
                }[_mo],
                3: {    # Null_val, colorrange, filename, mode
                    1: (20., 10, '4grsrq-800x800', (_mo - 1)),
                    2: (100., 20, '4grsrp-800x800', (_mo - 1)),
                    3: (0., 20, '4gsinr-800x800', (_mo - 1))
                }[_mo]
            }[_n_mo]

        _scanres = self.load_scanres(_net_mode)

        _sig_array_dict = {}
        if _plot_signal_array:
            _sig_array_dict = self.load_cells(_net_mode)

        _conf = []
        if _signal_type:
            _conf.append(_get_mode_config(_signal_type, _net_mode))
        else:
            for c in range(3):
                _conf.append(_get_mode_config((c + 1), _net_mode))

        for con in _conf:
            n_null, f_colo, o_name, _signal_type = con
            _radii = self.radii
            _max_ax = 0
            for i in range(self.N):
                if i in _scanres:
                    _cor_i = overflow_value((i + self.center), self.N)
                    _res = _scanres[i][_signal_type]
                    if _res is None:
                        _res = 0
                    else:
                        _res = round((n_null + _res), 2)
                        if _res > _max_ax:
                            _max_ax = _res
                    _radii[_cor_i] = _res

            _fig = plt.figure(figsize=(8, 8))
            _ax = _fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
            for label in _ax.get_yticklabels():
                _ax.figure.texts.append(label)
            if len(_sig_array_dict.keys()):               # Plot signal arrays if get data in ( sig_array not None )
                _radii_array = self.radii_array
                # Plot 2´nd axis ( Good Signal Arrays )
                # Source: https://stackoverflow.com/questions/19590103/add-second-axis-to-polar-plot
                _ax2 = _ax.figure.add_axes(_ax.get_position(), projection='polar',
                                         frameon=False, label='twin',
                                         theta_direction=_ax.get_theta_direction(),
                                         theta_offset=_ax.get_theta_offset())
                _map_null = _get_mode_config(1, _net_mode)[0]
                for _key in sorted(_sig_array_dict.keys()):
                    _cor_hdg_key = 0
                    for hdg_key in _sig_array_dict[_key]:
                        _cor_hdg_key = overflow_value((self.center + hdg_key), self.N)
                        _val = map_val(_key, 0, (40 * len(_sig_array_dict[_key])), 0, _max_ax)
                        _radii_array[_cor_hdg_key] = _val
                    _radii_array[_cor_hdg_key] = 0
                _ax2.set_yticklabels([])
                _ax2.grid(False)
                _ax2.xaxis.set_visible(False)
                _ax2.set_alpha(0.2)
                _ax2.fill_between(self.theta, _radii_array, color='black', alpha=0.2)

            _bars = _ax.bar(self.theta, _radii, width=self.width, bottom=0.0)
            for _r, _bar in zip(_radii, _bars):
                _bar.set_facecolor(cm.jet(_r / f_colo))
                _bar.set_alpha(0.9)
                time.sleep(0.001)                         # To get time for other threads

            _ax.set_rmin(-1)
            _ax.set_rmax(_max_ax)

            plt.savefig(self.html_images + o_name + '.png')
            plt.cla()
            plt.clf()
            plt.close(_fig)

            shutil.copy(self.html_images + o_name + '.png',
                        self.html_images + o_name + '-800x800' + '.png')
            time.sleep(0.1)                             # To get time for other threads

    def plot_signal_arrays(self, _net_mode):     # Plot signal array in a separately Plot
        # FIXME
        # plot axis get added and not separate axis ..
        # _radii_array = self.radii_array every irritation but doesnt wor .. hmpf
        # solution: Plot in bars not filled
        # FIXME END
        _sig_array_dict = self.load_cells(_net_mode)

        def _get_mode_config(_n_mo):
            return {
                2: (20., '3g_array-800x800'),
                3: (20., '4g_array-800x800')
            }[_n_mo]

        def _get_sig_array_color(_val):
            return {
                7: 'lawngreen',
                6: 'green',
                5: 'mediumspringgreen',
                4: 'yellowgreen',
                3: 'yellow',
                2: 'orange',
                1: 'red',
                0: 'black'
            }[int(round(_val / 3))]     # TODO better colors for the signal values

        if len(_sig_array_dict.keys()):  # Plot signal arrays if get data in ( sig_array not None )
            _plot_config = _get_mode_config(_net_mode)
            e_max = 0
            _fig = plt.figure(figsize=(8, 8))

            for _key in sorted(_sig_array_dict.keys()):
                _ax = _fig.add_axes([0.1, 0.1, 0.8, 0.8], projection='polar')
                # for _label in _ax.get_yticklabels():
                #     _ax.figure.texts.append(_label)
                _radii_array = []
                log("", 9)
                log("self.radii_array : " + str(self.radii_array), 9)
                _radii_array = self.radii_array

                log("Radi1 key:" + str(_key) + ' - Radi1' + str(_radii_array), 9)
                _cor_hdg_key = 0
                for _hdg_key in _sig_array_dict[_key]:
                    _cor_hdg_key = overflow_value((self.center + _hdg_key), self.N)
                    _radii_array[_cor_hdg_key] = _plot_config[0] + _key
                _radii_array[_cor_hdg_key] = 0

                _ax.grid(True)
                _ax.xaxis.set_visible(False)
                _col = _get_sig_array_color(_plot_config[0] + _key)     # FIXME
                if (_plot_config[0] + _key) > e_max:                    # FIXME
                    e_max = (_plot_config[0] + _key)                    # FIXME
                _ax.set_alpha(0.8)
                _ax.fill_between(self.theta, _radii_array, color=_col, alpha=0.8)
                _ax.set_rmin(0)
                _ax.set_rmax(e_max)
                log("", 9)
                log("Radi2 key:" + str(_key) + ' - Radi2' + str(_radii_array), 9)
                time.sleep(0.1)

            # ax.grid(True)

            # plt.savefig(self.html_images + plot_config[1] + '.png')   # TODO add space in website and change filename
            plt.savefig(config.html_root + 'test_' + str(_net_mode) + '.png')
            # shutil.copy(self.html_images + o_name + '.png',
            #             self.html_images + o_name + '-800x800' + '.png')

            plt.cla()
            plt.clf()
            plt.close(_fig)
            time.sleep(1)


if __name__ == '__main__':
    web = Data2Web()
    web.plot_lte_signals(_net_mode=2)
    web.plot_lte_signals(_net_mode=3)
