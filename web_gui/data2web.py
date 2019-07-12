import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import shutil
import config
import time
from etc.var import overflow_value, change_file_ext, map_val
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
        self.radii_array = []
        self.width = np.pi / 4 * np.random.rand(self.N)
        f = open(config.html_root + change_file_ext(config.html_lte_page, 'ba'), 'r')
        self.html_str_lte_page = f.read()
        f.close()
        for i in range(self.N):
            self.radii.append(-1)                   # -1 to show unscanned array in plot
            self.radii_array.append(0)
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

    def plot_lte_signals(self, net_mode=2, signal_type=0, plot_signal_array=True):
        # TODO Werte glaetten ( evtl )
        # TODO Performance !!!
        # TODO extra Plot for Signal Arrays
        # signal_type 1 = Plot Signal 'rsrq'
        # signal_type 2 = Plot Signal 'rsrp'
        # signal_type 3 = Plot Signal 'sinr'
        # signal_type 0 = Plot for all Signals
        # net_mode 2 = 3G
        # net_mode 3 = 4G

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

        scanres = {
            2: self.scan.scanres3G,
            3: self.scan.scanres4G
        }[net_mode]
        radii = self.radii
        width = self.width

        sig_array_dict = self.scan.get_signal_peak_in_range(scanres)
        if not plot_signal_array:
            sig_array_dict = {}

        conf = []
        if signal_type:
            conf.append(_get_mode_config(signal_type, net_mode))
        else:
            for c in range(3):
                conf.append(_get_mode_config((c + 1), net_mode))

        for con in conf:
            n_null, f_colo, o_name, signal_type = con
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

            fig = plt.figure(figsize=(8, 8))
            ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
            for label in ax.get_yticklabels():
                ax.figure.texts.append(label)
            if len(sig_array_dict.keys()):               # Plot signal arrays if get data in ( sig_array not None )

                map_null = _get_mode_config(1, net_mode)[0]
                for key in sorted(sig_array_dict.keys(), reverse=True):
                    radii_array = self.radii_array
                    # Plot 2´nd axis ( Good Signal Arrays )
                    # Source: https://stackoverflow.com/questions/19590103/add-second-axis-to-polar-plot
                    ax2 = ax.figure.add_axes(ax.get_position(), projection='polar',
                                             frameon=False, label='twin',
                                             theta_direction=ax.get_theta_direction(),
                                             theta_offset=ax.get_theta_offset())
                    for hdg_key in sig_array_dict[key]:
                        cor_hdg_key = overflow_value((self.center + hdg_key), self.N)
                        val = map_val((map_null + key), 0, map_null, 0, max_ax)
                        radii_array[cor_hdg_key] = val
                    ax2.set_yticklabels([])
                    ax2.grid(False)
                    ax2.xaxis.set_visible(False)
                    col = _get_sig_array_color(map_null + key)
                    ax2.set_alpha(0.2)
                    ax2.fill_between(self.theta, radii_array, color=col, alpha=0.2)

                    time.sleep(0.001)

            bars = ax.bar(self.theta, radii, width=width, bottom=0.0)
            for r, bar in zip(radii, bars):
                bar.set_facecolor(cm.jet(r / f_colo))
                bar.set_alpha(0.9)
                time.sleep(0.001)                         # To get time for other threads

            ax.set_rmin(-1)
            ax.set_rmax(max_ax)

            plt.savefig(self.html_images + o_name + '.png')
            plt.cla()
            plt.clf()
            plt.close(fig)

            shutil.copy(self.html_images + o_name + '.png',
                        self.html_images + o_name + '-800x800' + '.png')
            time.sleep(0.1)                             # To get time for other threads


