import time
import logging

import pandas as pd

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
        return self.float_1f(usdt), self.float_1f(fil), self.float_1f(btc)

    def reliable_get_balance(self):
        while True:
            try:
                return self.get_balance()
            except Exception as e:
                logging.error("reliable_get_balance error")
            time.sleep(2)

    def reliable_get_candlestick(self, symbol, period, size=200):
        while True:
            try:
                return market_client.get_candlestick(symbol, interval, size)
            except Exception as e:
                logging.error("reliable_get_candlestick error")
            time.sleep(2)

    def reliable_create_order(self, order_type=OrderType.BUY_MARKET, amount=1., price=1.292):
        while True:
            try:
                return trade_client.create_order(symbol=symbol, account_id=g_account_id,
                                                         order_type=order_type, source=OrderSource.API,
                                                         amount=amount, price=price)
            except Exception as e:
                logging.error("reliable_create_order error")
            time.sleep(2)

    def run(self):
        usdt = fil = btc = 0
        usdt, fil, btc = self.reliable_get_balance()
        logging.info("Holdings usdt={0} btc={1}".format(usdt, btc))

        kline_list = self.reliable_get_candlestick(symbol, interval, 300)

        global_data = Organized()
        global_data = self.parse_kline_data(kline_list)
        global_data.calculate_macd()

        last_index = global_data.get_len() - 2
        last_hist = global_data.get_hist(last_index)
        last_hist_pre = global_data.get_hist(last_index - 1)
        last_ts = global_data.get_timestamp(last_index)
        last_close = global_data.get_close(last_index)

        time = ''
        operation = 0
        hist = last_hist
        close = last_close
        count = 0
        cost_now = 5
        cost_used = 0
        cost_average = 0
        budget_available = usdt
        num_expected = 0
        num_actually = 0
        num_holding = btc

        last_price = 0  # 最后执行 BUY_DONE 的价格
        profit_at_least = 200 # 交易会产生各种手续费，至少保证盈利200，否则不卖

        operation = Operation.ERROR
        ops = lessdb.select_last_one()
        if ops:
            operation = ops[BTC_OPS_TABLE.OPERATION]
            if operation == Operation.SELL_DONE:
                count = 0
                # cost_now = 0
                cost_used = 0
                cost_average = 0
                budget_available = usdt
                num_expected = 0
                num_actually = 0
                num_holding = btc
                last_price = 0
            else:
                count = ops[BTC_OPS_TABLE.COUNT]
                # cost_now = ops[BTC_OPS_TABLE.COST_NOW]
                cost_used = ops[BTC_OPS_TABLE.COST_USED]
                cost_average = ops[BTC_OPS_TABLE.COST_AVERAGE]
                budget_available = ops[BTC_OPS_TABLE.BUDGET_AVAILABLE]
                num_expected = ops[BTC_OPS_TABLE.NUM_EXPECTED]
                num_actually = ops[BTC_OPS_TABLE.NUM_ACTUALLY]
                num_holding = ops[BTC_OPS_TABLE.NUM_HOLDING]
                ops = lessdb.select_by_operation(operation=Operation.BUY_DONE)
                last_price = ops[BTC_OPS_TABLE.CLOSE]

        global_data.calculate_macd()

        # Buy
        if last_hist_pre < 0 and last_hist > 0:
            if budget_available > cost_now:
                if last_price == 0 or (last_price > 0 and last_close < last_price):
                    # Buy 操作
                    order_id = self.reliable_create_order(order_type=OrderType.BUY_MARKET, amount=cost_now, price=1.292)
                    # 更新记录
                    usdt, fil, btc = self.reliable_get_balance()

                    count += 1
                    budget_available = usdt
                    num_expected = cost_now / (last_close + 200) # Market 价格一般高于收盘价，误差200
                    num_holding = btc
                    cost_used += cost_now
                    cost_average = cost_used / num_holding
                    last_price = last_close

                    values = [last_ts, Operation.BUY_DONE, hist, close, count, cost_now, cost_used, cost_average,
                              budget_available, num_expected, num_actually, num_holding]
                    lessdb.insert(values)

                    logging.info(
                        "BUY_DONE time={0} hist={1} close={2} count={3} cost_now={4} cost_used={5} cost_average={6} "
                        "budget_available={7} num_expected={8} num_actually={9} num_holding={10}".
                            format(time, hist, close, count, cost_now, cost_used, cost_average, budget_available,
                                   num_expected, num_actually, num_holding))
                else:
                    values = [last_ts, Operation.BUY_HOLDING, hist, close, count, cost_now, cost_used, cost_average,
                              budget_available, num_expected, num_actually, num_holding]
                    lessdb.insert(values)

                    logging.error(
                        "BUY_HOLDING time={0} hist={1} close={2} count={3} cost_now={4} cost_used={5} cost_average={6} "
                        "budget_available={7} num_expected={8} num_actually={9} num_holding={10}".
                            format(time, hist, close, count, cost_now, cost_used, cost_average, budget_available,
                                   num_expected, num_actually, num_holding))

            else:
                values = [last_ts, Operation.ERROR, hist, close, count, cost_now, cost_used, cost_average,
                          budget_available, num_expected, num_actually, num_holding]
                lessdb.insert(values)

                logging.error(
                    "BUY_ERROR time={0} hist={1} close={2} count={3} cost_now={4} cost_used={5} cost_average={6} "
                    "budget_available={7} num_expected={8} num_actually={9} num_holding={10}".
                        format(time, hist, close, count, cost_now, cost_used, cost_average, budget_available,
                               num_expected, num_actually, num_holding))
        # Sell
        elif last_hist_pre > 0 and last_hist < 0 and btc > 0:
            # 有利润才 sell
            if last_close - cost_average > profit_at_least:
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
                lessdb.insert(values)

                logging.error(
                    "SELL_DONE time={0} hist={1} close={2} count={3} cost_now={4} cost_used={5} cost_average={6} "
                    "budget_available={7} num_expected={8} num_actually={9} num_holding={10}".
                        format(time, hist, close, count, cost_now, cost_used, cost_average, budget_available,
                               num_expected, num_actually, num_holding))
            else:
                values = [last_ts, Operation.SELL_HOLDING, hist, close, count, cost_now, cost_used, cost_average,
                          budget_available, num_expected, num_actually, num_holding]
                lessdb.insert(values)

                logging.error(
                    "SELL_HOLDING time={0} hist={1} close={2} count={3} cost_now={4} cost_used={5} cost_average={6} "
                    "budget_available={7} num_expected={8} num_actually={9} num_holding={10}".
                        format(time, hist, close, count, cost_now, cost_used, cost_average, budget_available,
                               num_expected, num_actually, num_holding))


if __name__ == "__main__":
    lessismore = Lessismore()
    lessismore.init_log()

    while True:
        try:
            logging.info("run {0}-{1}".format(symbol, interval))
            lessismore.run()
        except Exception as err:
            logging.error(err)

        time.sleep(30)
