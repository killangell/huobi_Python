import time
import logging
from enum import IntEnum

import pandas as pd

from huobi.exception.huobi_api_exception import HuobiApiException
from my.lessdb import Lessdb, BTC_OPS_TABLE, Operation
from my.organized import Organized
from my.upath import UPath

from huobi.client.market import MarketClient
from huobi.client.account import AccountClient
from huobi.client.trade import TradeClient
from huobi.constant import *

account_client = AccountClient(api_key=g_api_key,
                               secret_key=g_secret_key)
market_client = MarketClient(init_log=True)
trade_client = TradeClient(api_key=g_api_key, secret_key=g_secret_key)

LESSDB_FILE = "less.db"
lessdb = Lessdb(LESSDB_FILE)

interval = CandlestickInterval.MIN30
symbol = "btcusdt"

log_file = "lessismore.log"
log_backup_file = "lessismore.log.backup"


class TradeDirection(IntEnum):
    LONG = 0,
    SHORT = 1,
    INVALID = 2,


trade_direction_his = TradeDirection.INVALID
trade_direction_cur = None
LOG_THROTTLE_COUNT = 20
log_throttle = 0

# 该买的时候，监控获得一个低于 average 的价格买入
# 该卖的时候，监控获得一个高于 average 的价格卖出
# 成功执行买入或者卖出的话，不需要监控
need_moniotr = True

# 每次买入的金额
cost_step_len = 50


class Lessismore:
    def __init__(self):
        pass

    def init_log(self):
        # backup a log copy, in case any error would be overwritten in a new run
        if UPath.is_file_exists(log_backup_file):
            UPath.remove(log_backup_file)

        if UPath.is_file_exists(log_file):
            UPath.rename(log_file, log_backup_file)

        logging.basicConfig(level=logging.INFO,  # 控制台打印的日志级别
                            filename=log_file,
                            filemode='w',  ##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                            # a是追加模式，默认如果不写的话，就是追加模式
                            format='%(asctime)s : %(message)s'
                            # '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                            # 日志格式
                            )

    def convert_timestamp(self, milliseconds):
        timestamp = float(milliseconds / 1000)
        time_local = time.localtime(timestamp)
        time_YmdHMS = time.strftime("%Y%m%d %H:%M", time_local)
        return time_YmdHMS

    def convert_timestamp_s(self, seconds):
        timestamp = int(seconds)
        time_local = time.localtime(timestamp)
        time_YmdHMS = time.strftime("%Y%m%d_%H%M%S", time_local)
        return time_YmdHMS

    def parse_kline_data(self, kline_list):
        org = Organized()
        # kline_list.sort(key=lambda x: x['id'])
        kline_list = kline_list.__reversed__()
        for kline in kline_list:
            org.id_list.append(kline.id)
            org.timestamp.append(self.convert_timestamp_s(kline.id))
            org.open_list.append(kline.open)
            org.close_list.append(kline.close)
            org.high_list.append(kline.high)
            org.low_list.append(kline.low)
        return org

    def float_1f(self, str='0.1'):
        return format(float(str), '.1f')

    def float_xf(self, str='0.1', precision=1):
        return format(float(str), '.{0}f'.format(precision))

    def get_balance(self):
        usdt = fil = btc = 0
        account_balance_list = account_client.get_account_balance()
        if account_balance_list and len(account_balance_list):
            for account_obj in account_balance_list:
                if account_obj.type == 'spot':  # 现货交易
                    # account_obj.print_object() # 打印全部
                    for item in account_obj.list:
                        # Currency: usdt
                        # Type: trade
                        # Balance: 61.771197560195410621
                        if item.type == 'trade':
                            if item.currency == 'usdt':
                                usdt = item.balance
                            if item.currency == 'fil':
                                fil = item.balance
                            if item.currency == 'btc':
                                btc = item.balance
        return float(self.float_1f(usdt)), float(self.float_1f(fil)), (float(self.float_xf(btc, 6)) - 0.000001)

    def reliable_get_balance(self):
        while True:
            try:
                return self.get_balance()
            except Exception as e:
                logging.error("reliable_get_balance error : " + e)
            time.sleep(2)

    def reliable_get_candlestick(self, symbol, period, size=200):
        while True:
            try:
                return market_client.get_candlestick(symbol, interval, size)
            except Exception as e:
                logging.error("reliable_get_candlestick error : " + e)
            time.sleep(2)

    def reliable_create_order(self, order_type=OrderType.BUY_MARKET, amount=1., price=1.292):
        while True:
            try:
                return trade_client.create_order(symbol=symbol, account_id=g_account_id,
                                                 order_type=order_type, source=OrderSource.API,
                                                 amount=amount, price=price)
            except Exception as e:
                logging.error("reliable_create_order error : " + e)
            time.sleep(2)

    def run(self):
        global trade_direction_cur
        global trade_direction_his
        global need_moniotr
        global log_throttle

        kline_list = self.reliable_get_candlestick(symbol, interval, 300)

        global_data = Organized()
        global_data = self.parse_kline_data(kline_list)
        global_data.calculate_macd()

        last_index = global_data.get_len() - 2
        last_hist = global_data.get_hist(last_index)
        last_hist_pre = global_data.get_hist(last_index - 1)
        last_ts = global_data.get_timestamp(last_index)
        last_close = global_data.get_close(last_index)
        real_time_close = global_data.get_close(global_data.get_len() - 1)

        if last_hist > 0:
            trade_direction_cur = TradeDirection.LONG
        elif last_hist < 0:
            trade_direction_cur = TradeDirection.SHORT
        else:
            logging.error("Invalid hist=0")
            return

        if (trade_direction_his != trade_direction_cur) or need_moniotr:
            usdt = fil = btc = 0
            usdt, fil, btc = self.reliable_get_balance()
            logging.info("Holdings usdt={0} btc={1} dir={2}".format(
                usdt, btc, 'long' if trade_direction_cur == TradeDirection.LONG else 'short'))

            operation = 0
            hist = last_hist
            close = last_close
            count = 0
            cost_now = cost_step_len
            cost_used = 0
            cost_average = 0
            budget_available = usdt
            num_expected = 0
            num_actually = 0
            num_holding = btc

            last_price = 0  # 最后执行 BUY_DONE 的价格
            profit_at_least = 200  # 交易会产生各种手续费，至少保证盈利200，否则不卖
            first_long_ts = ''
            first_long_price = 0

            operation = Operation.ERROR
            ops = lessdb.select_last_one()
            budget_available = usdt
            num_holding = btc
            if ops:
                operation = ops[BTC_OPS_TABLE.OPERATION]
                if operation == Operation.SELL_DONE:
                    count = 0
                    # cost_now = 0
                    cost_used = 0
                    cost_average = 0
                    num_expected = 0
                    num_actually = 0
                    last_price = 0
                    need_moniotr = False
                else:
                    count = ops[BTC_OPS_TABLE.COUNT]
                    # cost_now = ops[BTC_OPS_TABLE.COST_NOW]
                    cost_used = ops[BTC_OPS_TABLE.COST_USED]
                    cost_average = ops[BTC_OPS_TABLE.COST_AVERAGE]
                    num_expected = ops[BTC_OPS_TABLE.NUM_EXPECTED]
                    num_actually = ops[BTC_OPS_TABLE.NUM_ACTUALLY]
                    ops = lessdb.select_by_operation(operation=Operation.BUY_DONE)
                    if ops:
                        last_price = ops[BTC_OPS_TABLE.CLOSE]

            # Buy
            if trade_direction_cur == TradeDirection.LONG:
                # 检查是否已经买过了，因为程序可能重启过
                # 如果查询数据库里最近一次买的时间大于等于本周期内第一次变成绿柱的时间，则说明已经买过了
                # 如果当前不是第一个绿柱，则找到第一个绿柱
                # 如果当前收盘价格低于第一个绿柱，则是买入好时机，否则不操作
                # if last_hist_pre > 0:
                i = global_data.get_len() - 2
                while i > 0:
                    hist_tmp = global_data.get_hist(i)
                    if hist_tmp < 0:
                        # 第一个绿柱位置
                        i += 1
                        break
                    i -= 1
                first_long_ts = global_data.get_timestamp(i)
                first_long_price = global_data.get_close(i)
                ops = lessdb.select_by_operation(operation=Operation.BUY_DONE)
                if ops:
                    last_buy_done_time = ops[BTC_OPS_TABLE.TIME]
                    if last_buy_done_time:
                        last_buy_done_time_tmp = last_buy_done_time.replace('_', '')
                        first_long_ts_tmp = first_long_ts.replace('_', '')
                        last_buy_done_time_int = time.strptime(last_buy_done_time_tmp, '%Y%m%d%H%M%S')
                        firt_long_time_int = time.strptime(first_long_ts_tmp, '%Y%m%d%H%M%S')
                        time1 = time.mktime(firt_long_time_int)
                        time2 = time.mktime(last_buy_done_time_int)
                        if time1 <= time2:
                            # 每个周期只买一次2本周期内已经买过了，不再交易
                            logging.info(
                                "Already bought in this period on last_buy_done_tim={0}, first_long_time={1}".format(
                                    last_buy_done_time, first_long_ts))
                            logging.info(
                                "BUY_GIVEUP time={0} hist={1} close={2} count={3} cost_now={4} cost_used={5} cost_average={6} "
                                "budget_available={7} num_expected={8} num_actually={9} num_holding={10}".
                                    format(last_ts, hist, close, count, cost_now, cost_used, cost_average,
                                           budget_available,
                                           num_expected, num_actually, num_holding))

                            trade_direction_his = trade_direction_cur
                            need_moniotr = False
                            log_throttle = 0
                            return

                if budget_available > cost_now:
                    # 查询上次买入价格，如果当前收盘价格低于上次买入价格，则加仓
                    if (last_price == 0 and real_time_close < first_long_price) or \
                            (last_price > 0 and real_time_close < last_price):
                        # Buy 操作
                        order_id = self.reliable_create_order(order_type=OrderType.BUY_MARKET, amount=cost_now,
                                                              price=1.292)
                        # 更新记录
                        usdt, fil, btc = self.reliable_get_balance()

                        count += 1
                        budget_available = usdt
                        num_expected = cost_now / (last_close + 200)  # Market 价格一般高于收盘价，误差200
                        num_holding = btc
                        cost_used += cost_now
                        if num_holding > 0.0:
                            cost_average = cost_used / num_holding
                        else:
                            cost_average = 0

                        values = [last_ts, Operation.BUY_DONE, hist, close, count, cost_now, cost_used, cost_average,
                                  budget_available, num_expected, num_actually, num_holding]
                        lessdb.insert(values=values)

                        logging.info(
                            "BUY_DONE time={0} hist={1} close={2} count={3} cost_now={4} cost_used={5} cost_average={6} "
                            "budget_available={7} num_expected={8} num_actually={9} num_holding={10}".
                                format(last_ts, hist, close, count, cost_now, cost_used, cost_average, budget_available,
                                       num_expected, num_actually, num_holding))
                        need_moniotr = False
                        log_throttle = 0
                    else:
                        if (log_throttle % LOG_THROTTLE_COUNT) == 0:
                            values = [last_ts, Operation.BUY_HOLDING, hist, close, count, cost_now, cost_used,
                                      cost_average,
                                      budget_available, num_expected, num_actually, num_holding]
                            lessdb.insert(values=values)

                            logging.info(
                                "BUY_HOLDING time={0} hist={1} close={2} count={3} cost_now={4} cost_used={5} cost_average={6} "
                                "budget_available={7} num_expected={8} num_actually={9} num_holding={10}".
                                    format(last_ts, hist, close, count, cost_now, cost_used, cost_average,
                                           budget_available,
                                           num_expected, num_actually, num_holding))
                        need_moniotr = True
                        log_throttle += 1
                else:
                    if (log_throttle % LOG_THROTTLE_COUNT) == 0:
                        values = [last_ts, Operation.ERROR, hist, close, count, cost_now, cost_used, cost_average,
                                  budget_available, num_expected, num_actually, num_holding]
                        lessdb.insert(values=values)

                        logging.error(
                            "BUY_ERROR time={0} hist={1} close={2} count={3} cost_now={4} cost_used={5} cost_average={6} "
                            "budget_available={7} num_expected={8} num_actually={9} num_holding={10}".
                                format(last_ts, hist, close, count, cost_now, cost_used, cost_average, budget_available,
                                       num_expected, num_actually, num_holding))
                    need_moniotr = True
                    log_throttle += 1
            # Sell
            elif trade_direction_cur == TradeDirection.SHORT and btc > 0.0:
                # 有利润才 sell
                if real_time_close - cost_average > profit_at_least:
                    order_id = self.reliable_create_order(order_type=OrderType.SELL_MARKET, amount=btc, price=None)

                    usdt, fil, btc = self.reliable_get_balance()

                    count = 0
                    budget_available = usdt
                    num_expected = 0
                    num_holding = 0
                    cost_used = 0
                    cost_average = 0

                    values = [last_ts, Operation.SELL_DONE, hist, close, count, cost_now, cost_used, cost_average,
                              budget_available, num_expected, num_actually, num_holding]
                    lessdb.insert(values=values)

                    logging.info(
                        "SELL_DONE time={0} hist={1} close={2} count={3} cost_now={4} cost_used={5} cost_average={6} "
                        "budget_available={7} num_expected={8} num_actually={9} num_holding={10}".
                            format(last_ts, hist, close, count, cost_now, cost_used, cost_average, budget_available,
                                   num_expected, num_actually, num_holding))
                    need_moniotr = False
                    log_throttle = 0

                else:
                    if (log_throttle % LOG_THROTTLE_COUNT) == 0:
                        values = [last_ts, Operation.SELL_HOLDING, hist, close, count, cost_now, cost_used,
                                  cost_average,
                                  budget_available, num_expected, num_actually, num_holding]
                        lessdb.insert(values=values)

                        logging.error(
                            "SELL_HOLDING time={0} hist={1} close={2} count={3} cost_now={4} cost_used={5} cost_average={6} "
                            "budget_available={7} num_expected={8} num_actually={9} num_holding={10}".
                                format(last_ts, hist, close, count, cost_now, cost_used, cost_average, budget_available,
                                       num_expected, num_actually, num_holding))
                    need_moniotr = True
                    log_throttle += 1
        trade_direction_his = trade_direction_cur


if __name__ == "__main__":
    lessismore = Lessismore()
    lessismore.init_log()

    while True:
        try:
            print("{0}: run {1}-{2}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                                symbol, interval))
            lessismore.run()
        except HuobiApiException as hberr:
            logging.error(hberr)
        except Exception as err:
            logging.error(err)

        time.sleep(30)
