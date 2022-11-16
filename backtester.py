import os
import numpy as np


class NumTry:
    def read_file(self, file_path):
        lines_list = []
        with open(file_path, 'r') as file:
            for line in file:
                lines_list.append(line.strip())

        return lines_list

    def final_minus_initial_percent_change_0d(self, prev_val, new_val, multiplier):
        new = new_val
        old = prev_val
        tmp = ((new - old) / old) * multiplier

        return tmp

    def simple_moving_average_1d(self, data, period_sma):
        n = period_sma
        # --- calculate SMA
        ret = np.cumsum(data, dtype=float)
        ret[n:] = ret[n:] - ret[:-n]
        ret = ret[n - 1:] / n

        imputLen = len(data)
        outputLen = len(ret)
        lenDiff = imputLen - outputLen

        for k in range(lenDiff):
            var = ret[0]
            ret = np.insert(ret, 0, var)

        return ret

    def separate_price_and_signal_from_txt(self, list_of_lines, price_index=0, signal_index=1):
        price_list = []
        signal_list = []

        for line in list_of_lines:
            line_splitted = line.split(' ')
            price_list.append(line_splitted[price_index])
            signal_list.append(line_splitted[signal_index])

        return np.array(price_list).astype('float32'), np.array(signal_list).astype('float32')

    def get_list_of_files_in_dir(self, root_dir='res', file_extension='.txt'):
        list_of_files = []
        for file in os.listdir(root_dir):
            if file.endswith(file_extension):
                list_of_files.append(file)

        return list_of_files

    def list_of_files_to_dict(self, list_of_files):
        dict_of_files = {}
        for file_name in list_of_files:
            uuid_txt = file_name.split('__')[2]
            if uuid_txt not in dict_of_files.keys():
                dict_of_files[uuid_txt] = [file_name]
            else:
                dict_of_files[uuid_txt].append(file_name)

        return dict_of_files


class BtOrderManager1:
    def __init__(self, buy_thrsh, sel_thrsh, target, stop_loss):
        self.buy_thrsh = buy_thrsh
        self.sel_thrsh = sel_thrsh
        self.target = target
        self.stop_loss = stop_loss

        # states:
        self.long_pos = False
        self.short_pos = False
        self.entry_price = None
        self.entry_pl_index = None

        # outcomes
        self.pl_list = [0]
        self.long_trades_list = []
        self.short_trades_list = []

        self.num_win_long_trades = 0
        self.num_loss_long_trades = 0

        self.num_win_short_trades = 0
        self.num_los_short_trades = 0

    def is_open(self):
        if not self.long_pos and not self.short_pos:
            return False

        return True

    def check_threshold(self, signal_point):
        if signal_point >= self.buy_thrsh:
            return True, False

        if signal_point <= self.sel_thrsh:
            return False, True

        return False, False

    def go_long_1(self, price, number_of_shares=1):
        self.long_pos = True
        self.entry_price = price
        self.entry_pl_index = len(self.pl_list) - 1
        self.long_trades_list[-1] = 1

    def go_short_1(self, price, number_of_shares=1):
        self.short_pos = True
        self.entry_price = price
        self.entry_pl_index = len(self.pl_list) - 1
        self.short_trades_list[-1] = 1

    def check_for_target(self, price):
        if self.long_pos:
            if (((price - self.entry_price) / self.entry_price) * 100.0) > self.target:
                return True

        if self.short_pos:
            if (((self.entry_price - price) / self.entry_price) * 100.0) > self.target:
                return True

        return False

    def check_for_stop_loss(self, price):
        if self.long_pos:
            if (((price - self.entry_price) / self.entry_price) * 100.0) < -self.stop_loss:
                return True
        if self.short_pos:
            if (((self.entry_price - price) / self.entry_price) * 100.0) < -self.stop_loss:
                return True

        return False

    def exit_all(self, exit_reason):
        if self.long_pos:
            self.long_trades_list[-1] = -1

            if exit_reason == 'target':
                self.num_win_long_trades = self.num_win_long_trades + 1
            if exit_reason == 'stop_loss':
                self.num_loss_long_trades = self.num_loss_long_trades + 1

        if self.short_pos:
            self.short_trades_list[-1] = -1

            if exit_reason == 'target':
                self.num_win_short_trades = self.num_win_short_trades + 1
            if exit_reason == 'stop_loss':
                self.num_los_short_trades = self.num_los_short_trades + 1

        self.long_pos = False
        self.short_pos = False
        self.entry_price = None
        self.entry_pl_index = None

    def update_pl(self, price):
        if self.long_pos:
            self.pl_list.append(self.pl_list[self.entry_pl_index] + (price - self.entry_price))
        if self.short_pos:
            self.pl_list.append(self.pl_list[self.entry_pl_index] + (self.entry_price - price))

    def send_datapoint(self, price_point, signal_point):
        self.long_trades_list.append(0)
        self.short_trades_list.append(0)

        if not self.is_open():
            self.pl_list.append(self.pl_list[-1])
            buy_action, sell_action = self.check_threshold(signal_point)

            if buy_action:
                self.go_long_1(price_point)
            if sell_action:
                self.go_short_1(price_point)

        else:
            self.update_pl(price_point)

            if self.check_for_target(price_point):
                self.exit_all('target')

            if self.check_for_stop_loss(price_point):
                self.exit_all('stop_loss')

    def get_report(self):
        """
        self.pl_list = [0]
        self.long_trades_list = []
        self.short_trades_list = []

        self.num_win_long_trades = 0
        self.num_loss_long_trades = 0

        self.num_win_short_trades = 0
        self.num_los_short_trades = 0
        """
        # remove first item from self.pl_list
        self.pl_list.pop(0)

        results = {
        'pl_list': self.pl_list,
        'long_trades_list': self.long_trades_list,
        'short_trades_list': self.short_trades_list,

        'num_win_long_trades': self.num_win_long_trades,
        'num_loss_long_trades': self.num_loss_long_trades,

        'num_win_short_trades': self.num_win_short_trades,
        'num_los_short_trades': self.num_los_short_trades
        }

        return results


def remove_spikes(price_seq, max_percent_spike):
    tmp_prev = price_seq[0]
    no_spikes_price = []
    for k in range(1, len(price_seq)):
        percent_diff = abs(((price_seq[k] - price_seq[k - 1]) / price_seq[k - 1]) * 100.0)

        if percent_diff >= max_percent_spike:
            no_spikes_price.append(tmp_prev)
        else:
            no_spikes_price.append(price_seq[k])
            tmp_prev = price_seq[k]

    no_spikes_price = no_spikes_price + [no_spikes_price[-1]]

    return no_spikes_price


def append_string(csv_string, file_name):
    if '.txt' not in file_name:
        file_name = file_name + '.txt'

    file1 = open(file_name, "a")
    file1.write(csv_string + "\n")
    file1.close()


def get_min_max_average(lst):
    return min(lst), max(lst), sum(lst) / len(lst)

# ********************************************************************************************************************************
# ********************************************************************************************************************************
# ********************************************************************************************************************************


def main_bs_v03_backtester(buy_thrsh, sel_thrsh, target, stop_loss, save_timeseries=False, price_ma_interval=7, max_percent_spike=1.0):
    nt = NumTry()
    results_dir = 'res_bs'
    list_of_files = nt.get_list_of_files_in_dir(root_dir=results_dir)
    dict_of_files = nt.list_of_files_to_dict(list_of_files)
    for uuid_key in dict_of_files:
        min_pl_list = []
        max_pl_list = []
        eod_pl_list = []
        average_pl_list = []
        num_win_long_trades_list = []
        num_loss_long_trades_list = []
        num_win_short_trades_list = []
        num_los_short_trades_list = []

        list_of_files_for_model = dict_of_files[uuid_key]
        for file_name in list_of_files_for_model:
            lines = nt.read_file(results_dir + '/' + file_name)
            price, signal = nt.separate_price_and_signal_from_txt(lines)
            price = remove_spikes(price, max_percent_spike)
            price_ma = nt.simple_moving_average_1d(price, price_ma_interval)

            len_price = len(price)
            len_price_ma = len(price_ma)
            len_signal = len(signal)

            if len_price != len_price_ma:
                raise ValueError('error: not same length!')

            if len_price != len_signal:
                raise ValueError('error: not same length!')

            btom = BtOrderManager1(buy_thrsh, sel_thrsh, target, stop_loss)

            for price_ma_point, signal_point in zip(price_ma, signal):
                btom.send_datapoint(price_ma_point, signal_point)

            rep = btom.get_report()

            str_day = 'uuid_key {} file_name {} buy_thrsh {} sel_thrsh {} target {} stop_loss {} min_pl {} max_pl {} eod_pl {} average_pl {} num_win_long_trades {} num_loss_long_trades {} num_win_short_trades {} num_los_short_trades {}'.format(
                uuid_key, file_name, buy_thrsh, sel_thrsh, target, stop_loss, min(rep['pl_list']), max(rep['pl_list']), rep['pl_list'][-1], np.average(rep['pl_list']), rep['num_win_long_trades'], rep['num_loss_long_trades'], rep['num_win_short_trades'], rep['num_los_short_trades'])

            print(str_day)

            append_string(str_day, 'metrics_by_day.txt')

            if save_timeseries:
                column_stack = np.column_stack((
                    price,
                    price_ma,
                    signal,
                    rep['pl_list'],
                    rep['long_trades_list'],
                    rep['short_trades_list']
                    ))
                np.savetxt('bt/' + file_name.replace('.txt', '_BT.txt'), column_stack, fmt='%s')

            min_pl_list.append(min(rep['pl_list']))
            max_pl_list.append(max(rep['pl_list']))
            eod_pl_list.append(rep['pl_list'][-1])
            average_pl_list.append(np.average(rep['pl_list']))
            num_win_long_trades_list.append(rep['num_win_long_trades'])
            num_loss_long_trades_list.append(rep['num_loss_long_trades'])
            num_win_short_trades_list.append(rep['num_win_short_trades'])
            num_los_short_trades_list.append(rep['num_los_short_trades'])

        min_pl_min, min_pl_max, min_pl_avg = get_min_max_average(min_pl_list)
        max_pl_min, max_pl_max, max_pl_avg = get_min_max_average(max_pl_list)
        eod_pl_min, eod_pl_max, eod_pl_avg = get_min_max_average(eod_pl_list)
        average_pl_min, average_pl_max, average_pl_avg = get_min_max_average(average_pl_list)
        num_win_long_trades_min, num_win_long_trades_max, num_win_long_trades_avg = get_min_max_average(num_win_long_trades_list)
        num_loss_long_trades_min, num_loss_long_trades_max, num_loss_long_trades_avg = get_min_max_average(num_loss_long_trades_list)
        num_win_short_trades_min, num_win_short_trades_max, num_win_short_trades_avg = get_min_max_average(num_win_short_trades_list)
        num_los_short_trades_min, num_los_short_trades_max, num_los_short_trades_avg = get_min_max_average(num_los_short_trades_list)

        str_param = 'uuid_key {} buy_thrsh {} sel_thrsh {} target {} stop_loss {}'.format(uuid_key, buy_thrsh, sel_thrsh, target, stop_loss)
        str_min = 'min_pl_min {} min_pl_max {} min_pl_avg {}'.format(min_pl_min, min_pl_max, min_pl_avg)
        str_max = 'max_pl_min {} max_pl_max {} max_pl_avg {}'.format(max_pl_min, max_pl_max, max_pl_avg)
        str_eod = 'eod_pl_min {} eod_pl_max {} eod_pl_avg {}'.format(eod_pl_min, eod_pl_max, eod_pl_avg)
        str_aver = 'average_pl_min {} average_pl_max {} average_pl_avg {}'.format(average_pl_min, average_pl_max, average_pl_avg)
        str_win_long = 'num_win_long_trades_min {} num_win_long_trades_max {} num_win_long_trades_avg {}'.format(num_win_long_trades_min, num_win_long_trades_max, num_win_long_trades_avg)
        str_los_long = 'num_loss_long_trades_min {} num_loss_long_trades_max {} num_loss_long_trades_avg {}'.format(num_loss_long_trades_min, num_loss_long_trades_max, num_loss_long_trades_avg)
        str_win_short = 'num_win_short_trades_min {} num_win_short_trades_max {} num_win_short_trades_avg {}'.format(num_win_short_trades_min, num_win_short_trades_max, num_win_short_trades_avg)
        str_los_short = 'num_los_short_trades_min {} num_los_short_trades_max {} num_los_short_trades_avg {}'.format(num_los_short_trades_min, num_los_short_trades_max, num_los_short_trades_avg)

        str_total = '{} {} {} {} {} {} {} {} {}'.format(str_param, str_min, str_max, str_eod, str_aver, str_win_long, str_los_long, str_win_short, str_los_short)

        append_string(str_total, 'metrics_by_model.txt')


def main():
    buy_thrsh_list = [
        0.25,
        0.275,
        0.3,
        0.325,
        0.35,
        0.375,
        0.4
    ]

    sel_thrsh_list = [
        -0.25,
        -0.275,
        -0.3,
        -0.325,
        -0.35,
        -0.375,
        -0.4
    ]

    target_list = [0.2, 0.25, 0.3, 0.35, 0.4, 0.45]
    stop_loss_list = [0.2, 0.25, 0.3, 0.35, 0.4, 0.45]

    for bt in buy_thrsh_list:
        for st in sel_thrsh_list:
            for tr in target_list:
                for sl in stop_loss_list:
                    main_bs_v03_backtester(bt, st, tr, sl)

    return 0


if __name__ == '__main__':
    main()





