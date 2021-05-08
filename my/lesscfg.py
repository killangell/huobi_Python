# from enum import IntEnum
#
# from huobi.constant import CandlestickInterval
from my.config_helper import ConfigHelper, ConfigData


# class LessCfgCategory(IntEnum):
#     BTC = 0,
#     ETH = 1,
#     FIL = 2,
#
#
# lesscfg_category = LessCfgCategory.BTC
#
# if lesscfg_category == LessCfgCategory.BTC:
#     # 交易的币种
#     LESS_SYMBOL = 'btcusdt'
#     # 交易的周期
#     LESS_INTERVAL = CandlestickInterval.MIN30
#     # 每次买入的金额
#     LESS_BASE = 30
#     # 交易会产生各种手续费，至少保证盈利200，否则不卖
#     LESS_LEAST_PROFIT = 200
#     # 加仓差价，防止大跌的时候，本金在高位就被耗完
#     LESS_HOLDING_DIFF = 500
#     # 接针差价
#     LESS_PEAK_DIFF = 5000
# elif lesscfg_category == LessCfgCategory.ETH:
#     # 交易的币种
#     LESS_SYMBOL = 'ethusdt'
#     # 交易的周期
#     LESS_INTERVAL = CandlestickInterval.MIN30
#     # 每次买入的金额
#     LESS_BASE = 15
#     # 交易会产生各种手续费，至少保证盈利200，否则不卖
#     LESS_LEAST_PROFIT = 20
#     # 加仓差价，防止大跌的时候，本金在高位就被耗完
#     LESS_HOLDING_DIFF = 50
#     # 接针差价
#     LESS_PEAK_DIFF = 300
# elif lesscfg_category == LessCfgCategory.FIL:
#     # 交易的币种
#     LESS_SYMBOL = 'filusdt'
#     # 交易的周期
#     LESS_INTERVAL = CandlestickInterval.MIN30
#     # 每次买入的金额
#     LESS_BASE = 15
#     # 交易会产生各种手续费，至少保证盈利200，否则不卖
#     LESS_LEAST_PROFIT = 1
#     # 加仓差价，防止大跌的时候，本金在高位就被耗完
#     LESS_HOLDING_DIFF = 5
#     # 接针差价
#     LESS_PEAK_DIFF = 20


file = 'config.xml'
config_helper = ConfigHelper(file)
g_config_data = ConfigData()
ret = config_helper.init_root()
if not ret:
    print('Invalid config file')
    exit(0)

config_helper.parse(g_config_data)
ret = config_helper.check(g_config_data)
if not ret:
    print('Invalid config data')
    exit(0)

LESS_ACCESS_KEY = g_config_data._access_key
LESS_SECRET_KEY = g_config_data._secret_key
LESS_ACCOUNT_ID = g_config_data._account_id

LESS_SYMBOL = g_config_data._symbol
LESS_INTERVAL = g_config_data._interval
LESS_BASE = int(g_config_data._base)
LESS_MAX_COUNT = int(g_config_data._max_count)
LESS_LEAST_PROFIT = int(g_config_data._least_profit)
LESS_ADD_DIFF = int(g_config_data._add_diff)
LESS_PEAK_DIFF = int(g_config_data._peak_diff)