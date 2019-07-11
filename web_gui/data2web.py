import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import shutil
import config
from etc.var import overflow_value
from etc.log import log


class Data2Web:
    def __init__(self, scan_cl, auto_loop=True):
        self.run_trigger = False
        self.scan = scan_cl
        # HTML Location
        self.html_images = config.html_images
        # Signal Plot
        self.N = self.scan.N
        self.val_range = self.scan.val_range
        self.theta = np.arange(0.0, 2 * np.pi, 2 * np.pi / self.N)
        self.center = int((self.N - self.val_range) / 2)
        self.radii = []
        self.width = np.pi / 4 * np.random.rand(self.N)
        f = open(config.html_root + config.html_lte_page.replace('.html', '.ba'), 'r')
        self.html_str_lte_page = f.read()
        f.close()
        for i in range(self.N):
            self.radii.append(-1)           # -1 to show unscanned array in plot
        for i in range(len(self.width)):
            self.width[i] = 6 / self.N

    def write_plmn_list2web(self, get_new_plmn=False):
        if get_new_plmn:
            self.scan.get_plmn_list()
        plmn = self.scan.plmn_list
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

    def plot_lte_signals(self, net_mode=2, signal_type=0):
        # TODO Werte glaetten ( evtl )
        # TODO Web Ausgabe in extra Class, extra thread ..

        # signal_type 1 = Plot Signal 'rsrq'
        # signal_type 2 = Plot Signal 'rsrp'
        # signal_type 3 = Plot Signal 'sinr'
        # signal_type 0 = Plot for all Signals
        # net_mode 2 = 3G
        # net_mode 3 = 4G
        scanres = {
            2: self.scan.scanres3G,
            3: self.scan.scanres4G
        }[net_mode]
        radii = self.radii
        width = self.width

        def _get_mode_config(mo, n_mo):
            return {
                2: {    # Null_val, colorrange, filename, mode
                    1: (20., 10, '3gecio-800x800', (mo - 1)),
                    2: (120., 60, '3grscp-800x800', (mo - 1)),
                    3: (110., 40, '3grssi-800x800', (mo - 1))
                }[mo],
                3: {    # Null_val, colorrange, filename, mode
                    1: (20., 10, '4grsrq-800x800', (mo - 1)),
                    2: (100., 20, '4grsrp-800x800', (mo - 1)),
                    3: (0., 20, '4gsinr-800x800', (mo - 1))
                }[mo]
            }[n_mo]
        conf = []
        if signal_type:
            conf.append(_get_mode_config(signal_type, net_mode))
        else:
            for c in range(3):
                conf.append(_get_mode_config((c + 1), net_mode))

        for con in conf:
            n_null, f_colo, o_name, signal_type = con
            # log("Start {}".format(con))
            max_ax = 0
            for i in range(self.N):
                if i in scanres:
                    cor_i = overflow_value((i + self.center), self.N)
                    _res = scanres[i][signal_type]
                    if _res is None:
                        _res = 0
                    else:
                        _res = round((n_null + _res), 2)
                        if _res > max_ax:
                            max_ax = _res
                    radii[cor_i] = _res
                    # log("radi> {} - i {} - sig {}".format(radii[cor_i], i, signal_type), 9)

            fig = plt.figure(figsize=(8, 8))
            ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
            # max_foo = int(max(radii))
            # c = np.ones((max_foo, max_foo)) + np.arange(max_foo).reshape(max_foo, 1)
            # ap = ax.pcolormesh(c)
            # ax.set_alpha(0.2)
            # plt.colorbar(ap)
            bars = ax.bar(self.theta, radii, width=width, bottom=0.0)
            for r, bar in zip(radii, bars):
                bar.set_facecolor(cm.jet(r / f_colo))
                bar.set_alpha(0.9)

            ax.set_rmin(-1)
            ax.set_rmax(max_ax)

            plt.savefig(self.html_images + o_name + '.png')
            plt.close(fig)
            shutil.copy(self.html_images + o_name + '.png',
                        self.html_images + o_name + '-800x800' + '.png')


