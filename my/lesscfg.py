from enum import IntEnum

from huobi.constant import CandlestickInterval


class LessCfgCategory(IntEnum):
    BTC = 0,
    ETH = 1,
    FIL = 2,


lesscfg_category = LessCfgCategory.BTC

if lesscfg_category == LessCfgCategory.BTC:
    # 交易的币种
    LESS_SYMBOL = 'btcusdt'
    # 交易的周期
    LESS_INTERVAL = CandlestickInterval.MIN30
    # 每次买入的金额
    LESS_STEP_LEN = 30
    # 交易会产生各种手续费，至少保证盈利200，否则不卖
    LESS_LEAST_PROFIT = 200
    # 加仓差价，防止大跌的时候，本金在高位就被耗完
    LESS_HOLDING_DIFF = 500
    # 接针差价
    LESS_PEAK_DIFF = 5000
elif lesscfg_category == LessCfgCategory.ETH:
    # 交易的币种
    LESS_SYMBOL = 'ethusdt'
    # 交易的周期
    LESS_INTERVAL = CandlestickInterval.MIN30
    # 每次买入的金额
    LESS_STEP_LEN = 15
    # 交易会产生各种手续费，至少保证盈利200，否则不卖
    LESS_LEAST_PROFIT = 20
    # 加仓差价，防止大跌的时候，本金在高位就被耗完
    LESS_HOLDING_DIFF = 50
    # 接针差价
    LESS_PEAK_DIFF = 300
elif lesscfg_category == LessCfgCategory.FIL:
    # 交易的币种
    LESS_SYMBOL = 'filusdt'
    # 交易的周期
    LESS_INTERVAL = CandlestickInterval.MIN30
    # 每次买入的金额
    LESS_STEP_LEN = 15
    # 交易会产生各种手续费，至少保证盈利200，否则不卖
    LESS_LEAST_PROFIT = 1
    # 加仓差价，防止大跌的时候，本金在高位就被耗完
    LESS_HOLDING_DIFF = 5
    # 接针差价
    LESS_PEAK_DIFF = 20
