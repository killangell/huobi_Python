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



