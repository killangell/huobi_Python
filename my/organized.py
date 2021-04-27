import talib
from pandas import np


class Organized:
    def __init__(self):
        self._id_list = []
        self._timestamp = []
        self._open_list = []
        self._close_list = []
        self._high_list = []
        self._low_list = []
        self._hist_list = []  # MACD
        self._ma_list = [[0 * 60000]] * 500
        self._ema_list = [[0 * 60000]] * 500
        self._slowk_list = []
        self._slowd_list = []
        self._fastk_list = []
        self._fastd_list = []

    def get_len(self):
        return len(self._id_list)

    def get_id(self, index):
        return self._id_list[index]

    def get_timestamp(self, index):
        return self._timestamp[index]

    def get_hist(self, index):
        return self._hist_list[index]

    def get_open(self, index):
        return self._open_list[index]

    def get_close(self, index):
        return self._close_list[index]

    def get_high(self, index):
        return self._high_list[index]

    def get_low(self, index):
        return self._low_list[index]

    def get_ema(self, period, index):
        return self._ema_list[period][index]

    def get_ma(self, period, index):
        return self._ma_list[period][index]

    def get_slowk(self, index):
        return self._slowk_list[index]

    def get_slowd(self, index):
        return self._slowd_list[index]

    def get_fastk(self, index):
        return self._fastk_list[index]

    def get_fastd(self, index):
        return self._fastd_list[index]

    def calculate_ema(self, xma_period):
        xma_list = talib.EMA(np.array(self._close_list), timeperiod=xma_period)
        self._ema_list[xma_period] = xma_list

    def calculate_ma(self, xma_period):
        xma_list = talib.MA(np.array(self._close_list), timeperiod=xma_period)
        self._ma_list[xma_period] = xma_list

    def calculate_macd(self, fastperiod=12, slowperiod=26, signalperiod=9):
        macd, macd_signal, macd_hist = talib.MACD(np.array(self._close_list), fastperiod, slowperiod, signalperiod)
        self._hist_list = macd_hist
        return macd, macd_signal, macd_hist

    def calculate_kdj(self):
        self._slowk_list, self._slowd_list = talib.STOCH(np.array(self._high_list),
                                                         np.array(self._low_list),
                                                         np.array(self._close_list),
                                                         fastk_period=9,
                                                         slowk_period=3,
                                                         slowk_matype=0,
                                                         slowd_period=3,
                                                         slowd_matype=0)

    def calculate_stochrsi(self):
        self._fastk_list, self._fastd_list = talib.STOCHRSI(
            np.array(self._close_list), timeperiod=14, fastk_period=3, fastd_period=3, fastd_matype=0)

    def get_latest_first_hist_position(self, long=True):
        i = self.get_len() - 2
        # 如果当前趋势为 short，查找第一个long的位置，需要排除当前所有的空头k线
        if long:
            if self.get_hist(i) < 0:
                while i > 0:
                    if self.get_hist(i) > 0:
                        break
                    i -= 1
        # 如果当前趋势为 long，查找第一个short的位置，需要排除当前所有的多头k线
        else:
            if self.get_hist(i) > 0:
                while i > 0:
                    if self.get_hist(i) < 0:
                        break
                    i -= 1
        while i > 0:
            hist_tmp = self.get_hist(i)
            if (long and hist_tmp < 0) or (not long and hist_tmp > 0):
                # <0 第一个绿柱位置; >0 第一个红柱位置
                i += 1
                break
            i -= 1

        if i > 0:
            return i
        else:
            return 0

    @property
    def ema_list(self):
        return self._ema_list

    @property
    def ma_list(self):
        return self._ma_list

    @property
    def open_list(self):
        return self._open_list

    @property
    def close_list(self):
        return self._close_list

    @property
    def high_list(self):
        return self._high_list

    @property
    def low_list(self):
        return self._low_list

    @property
    def id_list(self):
        return self._id_list

    @property
    def timestamp(self):
        return self._timestamp
