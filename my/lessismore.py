import os, shutil
import time
import logging
from enum import IntEnum

from huobi.exception.huobi_api_exception import HuobiApiException
from my.lesscfg import LESS_SYMBOL, LESS_INTERVAL, LESS_BASE, LESS_MAX_COUNT, LESS_LEAST_PROFIT, LESS_ADD_DIFF, \
    LESS_PEAK_DIFF
from my.lessdb import Lessdb, BTC_OPS_TABLE, Operation
from my.organized import Organized
from my.upath import UPath

from huobi.client.market import MarketClient
from huobi.client.account import AccountClient
from huobi.client.trade import TradeClient
from huobi.constant import *
from my.utils import Utils

account_client = AccountClient(api_key=g_api_key,
                               secret_key=g_secret_key)
market_client = MarketClient(init_log=True)
trade_client = TradeClient(api_key=g_api_key, secret_key=g_secret_key)


class LessTradeDirection(IntEnum):
    LONG = 0,
    SHORT = 1,
    INVALID = 2,


symbol = LESS_SYMBOL
interval = LESS_INTERVAL
LOG_THROTTLE_COUNT = 1
LESSDB_FILE = "less_{0}.db".format(symbol)


class Lessismore:
    def __init__(self):
        self._cur_hist = 0
        self._cur_timestamp = ''
        self._cur_close = 0
        #
        self._count = 0
        self._cost_now = LESS_BASE
        self._cost_used = 0
        self._cost_average = 0
        self._num_expected = 0
        self._num_actually = 0
        self._num_holding = 0
        self._budget_available = 0
        self._real_time_close = 0
        #
        self._last_price = 0
        self._last_hist = 0  # 用于表示上次购买的时候趋势是long 还是 short
        self._last_time = ''
        #
        self._trade_direction_his = LessTradeDirection.INVALID
        self._trade_direction_cur = LessTradeDirection.INVALID
        self._log_throttle = 0
        # 该买的时候，监控获得一个低于 average 的价格买入
        # 该卖的时候，监控获得一个高于 average 的价格卖出
        # 成功执行买入或者卖出的话，不需要监控
        self._need_monitor = True
        self._profit_at_least = LESS_LEAST_PROFIT
        self._add_diff = LESS_ADD_DIFF
        # 把钱分为多少份进行购买
        self._max_count = LESS_MAX_COUNT

        print("symbol = ", symbol)
        print("interval = ", interval)
        print("cost_now = ", self._cost_now)
        print("max_count = ", self._max_count)
        print("profit_at_least = ", self._profit_at_least)
        print("add_diff = ", self._add_diff)
        print("peak_diff = ", LESS_PEAK_DIFF)
        print("LESSDB_FILE = " + LESSDB_FILE)
        self._lessdb = Lessdb(LESSDB_FILE)

    def init_log(self):
        log_path = 'logs'
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        log_file_backup = log_path + '\/' + symbol + '_' + time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
        log_file_backup += '.log'

        log_file = "lessismore_" + symbol + ".log"
        if os.path.exists(log_file):
            print('log_file_backup = ', log_file_backup)
            shutil.move(log_file, log_file_backup)

        logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
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

    def precision_x(self, str='0.123456789', precision=6):
        if str == '0' or str == 0:
            return 0
        s1 = str
        s1_list = s1.split('.')
        s1_new = s1_list[0] + '.' + s1_list[1][:precision]
        return s1_new

    def get_balance(self, symbol='btcusdt'):
        usdt = eth = btc = fil = 0
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
                            if item.currency == 'eth':
                                eth = item.balance
                            if item.currency == 'btc':
                                btc = item.balance
                            if item.currency == 'fil':
                                fil = item.balance
        else:
            return 0, 0
        if symbol == 'btcusdt':
            return float(self.float_1f(usdt)), float(self.precision_x(btc, 6))
        elif symbol == 'ethusdt':
            return float(self.float_1f(usdt)), float(self.precision_x(eth, 4))
        elif symbol == 'filusdt':
            return float(self.float_1f(usdt)), float(self.precision_x(fil, 4))

    def reliable_get_balance(self):
        while True:
            try:
                return self.get_balance(symbol)
            except HuobiApiException as e:
                logging.error("info: reliable_get_balance huobi error : " + e.error_message)
            except Exception as e:
                logging.error("info: reliable_get_balance error : " + str(e))
            time.sleep(5)

    def reliable_get_candlestick(self, symbol, period, size=200):
        while True:
            try:
                return market_client.get_candlestick(symbol, interval, size)
            except HuobiApiException as e:
                logging.error("info: reliable_get_candlestick huobi error : " + e.error_message)
            except Exception as e:
                logging.error("info: reliable_get_candlestick error : " + str(e))
            time.sleep(5)

    def reliable_create_order(self, order_type=OrderType.BUY_MARKET, amount=1., price=1.292):
        while True:
            try:
                return trade_client.create_order(symbol=symbol, account_id=g_account_id,
                                                 order_type=order_type, source=OrderSource.API,
                                                 amount=amount, price=price)
            except HuobiApiException as e:
                logging.error(
                    "info: reliable_create_order huobi error : {0}, {1}, {2}".format(order_type, amount,
                                                                                     e.error_message))
                if e.error_message.index("not enough") > 0:
                    if symbol == "btcusdt":
                        amount -= 0.000001
                    elif symbol == "ethusdt":
                        amount -= 0.0001
                    elif symbol == "filusdt":
                        amount -= 0.0001
                    logging.error("info: reliable_create_order reduce amount to {0}, {1}".format(order_type, amount))
            except Exception as e:
                logging.error("info: reliable_create_order error : {0}, {1}, {2}".format(order_type, amount, e))
            time.sleep(3)

    def get_time_seconds(self, time_str):
        time_str_tmp = time_str.replace('_', '')
        time1_str_tmp_int = time.strptime(time_str_tmp, '%Y%m%d%H%M%S')
        return time.mktime(time1_str_tmp_int)

    def buy_done(self, usdt=None):
        logging.debug("info: buy_done usdt={0}".format(usdt))
        if usdt is None:
            usdt = self._cost_now
        # Buy 操作
        order_id = self.reliable_create_order(order_type=OrderType.BUY_MARKET, amount=usdt,
                                              price=1.292)
        # 更新记录
        self._budget_available, self._num_holding = self.reliable_get_balance()
        logging.debug("info: buy_done budget_available={0} num_holding={1}".format(self._budget_available,
                                                                                   self._num_holding))

        self._count += 1
        self._num_expected = usdt / self._real_time_close
        self._cost_used += usdt
        if self._num_holding > 0.0:
            self._cost_average = self._cost_used / self._num_holding
        else:
            self._cost_average = 0

        values = [self._cur_timestamp, Operation.BUY_DONE, self._cur_hist, self._real_time_close, self._count,
                  self._cost_now, self._cost_used, self._cost_average, self._budget_available, self._num_expected,
                  self._num_actually, self._num_holding]
        self._lessdb.insert(values=values)

        logging.info(
            "info: BUY_DONE time={0} hist={1} close={2} real_time_close={3} count={4} cost_now={5} cost_used={6} "
            "cost_average={7} budget_available={8} num_expected={9} actually={10} num_holding={11} usdt={12}".
                format(self._cur_timestamp, self._cur_hist, self._cur_close, self._real_time_close,
                       self._count, self._cost_now, self._cost_used, self._cost_average,
                       self._budget_available, self._num_expected, self._num_actually, self._num_holding, usdt))

    def buy_holding(self, next_usdt=0):
        logging.debug("debug: buy_holding next_usdt={0}".format(next_usdt))
        if (self._log_throttle % LOG_THROTTLE_COUNT) == 0:
            # values = [self._cur_timestamp, Operation.BUY_HOLDING, self._cur_hist, self._real_time_close,
            #           self._count, self._cost_now, self._cost_used, self._cost_average, self._budget_available,
            #           self._num_expected, self._num_actually, self._num_holding]
            # self._lessdb.insert(values=values)

            logging.info(
                "info: BUY_HOLDING time={0} hist={1} close={2} real_time_close={3} count={4} cost_now={5} cost_used={6} "
                "cost_average={7} budget_available={8} num_expected={9} num_actually={10} num_holding={11} "
                "waiting_close={12} next_usdt={13}".
                    format(self._cur_timestamp, self._cur_hist, self._cur_close, self._real_time_close,
                           self._count, self._cost_now, self._cost_used, self._cost_average,
                           self._budget_available, self._num_expected, self._num_actually, self._num_holding,
                           self._last_price - self._add_diff, next_usdt))

    def buy_error(self, next_usdt=0):
        logging.debug("debug: buy_error next_usdt={0}".format(next_usdt))
        if (self._log_throttle % LOG_THROTTLE_COUNT) == 0:
            # values = [self._cur_timestamp, Operation.BUY_ERROR, self._cur_hist, self._real_time_close, self._count,
            #           self._cost_now, self._cost_used, self._cost_average, self._budget_available, self._num_expected,
            #           self._num_actually, self._num_holding]
            # self._lessdb.insert(values=values)

            logging.error(
                "info: BUY_ERROR time={0} hist={1} close={2}, real_time_close={3} count={4} cost_now={5} cost_used={6} "
                "cost_average={7} budget_available={8} num_expected={9} num_actually={10} num_holding={11} "
                "next_usdt={12}".
                    format(self._cur_timestamp, self._cur_hist, self._cur_close, self._real_time_close, self._count,
                           self._cost_now, self._cost_used, self._cost_average, self._budget_available,
                           self._num_expected, self._num_actually, self._num_holding, next_usdt))

    def sell_done(self):
        logging.debug("info: sell_done")
        order_id = self.reliable_create_order(order_type=OrderType.SELL_MARKET, amount=self._num_holding,
                                              price=1.292)

        usdt_available, coin_available = self.reliable_get_balance()
        self.set_running_data(usdt=usdt_available, coin_num=0, ops=None)
        logging.debug("info: sell_done  budget_available={0} num_holding={1}".format(self._budget_available,
                                                                                     self._num_holding))

        values = [self._cur_timestamp, Operation.SELL_DONE, self._cur_hist, self._real_time_close, self._count,
                  self._cost_now, self._cost_used, self._cost_average, self._budget_available, self._num_expected,
                  self._num_actually, self._num_holding]
        self._lessdb.insert(values=values)

        logging.info(
            "info: SELL_DONE time={0} hist={1} close={2} real_time_close={3} count={4} cost_now={5} cost_used={6} "
            "cost_average={7} budget_available={8} num_expected={9} num_actually={10} num_holding={11}".
                format(self._cur_timestamp, self._cur_hist, self._cur_close, self._real_time_close, self._count,
                       self._cost_now, self._cost_used, self._cost_average, self._budget_available,
                       self._num_expected, self._num_actually, self._num_holding))

    def sell_holding(self):
        logging.debug("info: sell_holding")
        if (self._log_throttle % LOG_THROTTLE_COUNT) == 0:
            # values = [self._cur_timestamp, Operation.SELL_HOLDING, self._cur_hist, self._real_time_close,
            #           self._count, self._cost_now, self._cost_used, self._cost_average, self._budget_available,
            #           self._num_expected, self._num_actually, self._num_holding]
            # self._lessdb.insert(values=values)

            logging.error(
                "info: SELL_HOLDING time={0} hist={1} close={2} real_time_close={3} count={4} cost_now={5} cost_used={6} "
                "cost_average={7} budget_available={8} num_expected={9} num_actually={10} num_holding={11} "
                "waiting_close={12}".
                    format(self._cur_timestamp, self._cur_hist, self._cur_close, self._real_time_close, self._count,
                           self._cost_now, self._cost_used, self._cost_average, self._budget_available,
                           self._num_expected, self._num_actually, self._num_holding,
                           self._cost_average + self._profit_at_least))

    def set_running_data(self, usdt=None, coin_num=None, ops=None):
        if usdt is not None:
            self._budget_available = usdt
        if coin_num is not None:
            self._num_holding = coin_num
        if ops is not None:
            self._count = ops[BTC_OPS_TABLE.COUNT]
            self._cost_used = ops[BTC_OPS_TABLE.COST_USED]
            self._cost_average = ops[BTC_OPS_TABLE.COST_AVERAGE]
            self._num_expected = ops[BTC_OPS_TABLE.NUM_EXPECTED]
            self._num_actually = ops[BTC_OPS_TABLE.NUM_ACTUALLY]
            self._last_price = ops[BTC_OPS_TABLE.CLOSE]
            self._last_hist = ops[BTC_OPS_TABLE.HIST]
            self._last_time = ops[BTC_OPS_TABLE.TIME]
        else:
            self._count = 0
            self._cost_used = 0
            self._cost_average = 0
            self._num_expected = 0
            self._num_actually = 0
            self._last_price = 0
            self._last_hist = 0
            self._last_time = ''

    def try_buy(self, condition=None):
        logging.debug("debug: try_buy condition={0}".format(condition))
        if condition is None:
            condition = True
        next_usdt = float(self.get_next_usdt())
        if condition:
            if self._budget_available > next_usdt:
                self.buy_done(next_usdt)
                return Operation.BUY_DONE
            elif self._budget_available > 1.0:
                usdt_avail_str = "{0}".format(self._budget_available)
                usdt_avail = float(Utils.precision_x(usdt_avail_str, 2))
                self.buy_done(usdt_avail)
                return Operation.BUY_DONE
            else:
                self.buy_error(next_usdt)
                return Operation.BUY_ERROR
        else:
            self.buy_holding(next_usdt)
            return Operation.BUY_HOLDING

    def try_sell(self, condition=None):
        logging.debug("debug: try_sell condition={0}".format(condition))
        if condition is None:
            condition = self._real_time_close - self._cost_average > self._profit_at_least
        if condition:
            self.sell_done()
        else:
            self.sell_holding()

    def get_next_usdt(self):
        logging.debug("debug: get_next_usdt cost_now={0} max_count={1} usdt_total={2}".format(
            self._cost_now, self._max_count, self._cost_used + self._budget_available))
        ret_list = []
        ret_list = Utils.get_list_of_arit_seq(self._cost_now, self._max_count, self._cost_used + self._budget_available)
        ret_str = "{0}".format(ret_list[self._count])
        ret = Utils.precision_x(ret_str, 2)
        logging.debug("debug: get_next_usdt ret_list={0}".format(ret_list))
        logging.debug("debug: get_next_usdt count={0} ret_str={1} ret={2}".format(self._count, ret_str, ret))
        return ret

    def run(self):
        logging.debug("debug: started to run")
        kline_list = self.reliable_get_candlestick(symbol, interval, 300)
        logging.debug("debug: got kline_list")

        global_data = Organized()
        global_data = self.parse_kline_data(kline_list)
        global_data.calculate_macd()
        logging.debug("debug: parsed kline and calculated macd")

        last_index = global_data.get_len() - 2

        self._cur_hist = global_data.get_hist(last_index)
        self._cur_timestamp = global_data.get_timestamp(last_index)
        self._cur_close = global_data.get_close(last_index)
        self._real_time_close = global_data.get_close(global_data.get_len() - 1)

        if self._cur_hist > 0:
            self._trade_direction_cur = LessTradeDirection.LONG
        elif self._cur_hist < 0:
            self._trade_direction_cur = LessTradeDirection.SHORT
        else:
            logging.error("info: Invalid hist=0")
            return

        logging.debug("debug: trade_direction_his={0}, trade_direction_cur={1}, need_monitor={2}".format(
            self._trade_direction_his, self._trade_direction_cur, self._need_monitor))
        if (self._trade_direction_his != self._trade_direction_cur) or self._need_monitor:
            logging.debug("debug: trade_direction_his != trade_direction_cur")
            # 如果上次是 SELL_HOLING 状态 self._log_throttle 已经不是 0
            # 在多空转换的时候，如果现在是 BUY_HOLDING 状态，则可能无法打印第一次的log
            # 所以需要将 self._log_throttle 清 0
            if self._trade_direction_his != self._trade_direction_cur:
                self._log_throttle = 0

            usdt_available, coin_available = self.reliable_get_balance()
            self.set_running_data(usdt=usdt_available, coin_num=coin_available, ops=None)
            logging.debug("debug: got balance")

            first_long_ts = ''
            first_long_price = 0

            ops_buy_done = self._lessdb.select_last_one_by_operation(operation=Operation.BUY_DONE)
            logging.debug("debug: last_buy_done={0}".format(ops_buy_done))
            ops_sell_done = self._lessdb.select_last_one_by_operation(operation=Operation.SELL_DONE)
            logging.debug("debug: last_sell_done={0}".format(ops_sell_done))

            if (self._log_throttle % LOG_THROTTLE_COUNT) == 0:
                logging.info("info: " + time.strftime('%Y-%m-%d_%H_%M_%S', time.localtime()))
                logging.info("info: symbol={0} usdt={1} coin_num={2} dir={3}".format(
                    symbol, usdt_available, coin_available,
                    'long' if self._trade_direction_cur == LessTradeDirection.LONG else 'short'))
                logging.info("info: ops_buy_done={0}".format(ops_buy_done))
                logging.info("info: ops_sell_done={0}".format(ops_sell_done))

            if ops_buy_done and not ops_sell_done:
                logging.debug("debug: buy_done and not sell_done")
                self.set_running_data(ops=ops_buy_done)
            if ops_buy_done and ops_sell_done:
                logging.debug("debug: buy_done and sell_done")
                buy_done_time_str = ops_buy_done[BTC_OPS_TABLE.TIME]
                sell_down_time_str = ops_sell_done[BTC_OPS_TABLE.TIME]
                buy_done_time = self.get_time_seconds(buy_done_time_str)
                sell_down_time = self.get_time_seconds(sell_down_time_str)
                if (buy_done_time > sell_down_time) and (self._num_holding > 0):
                    self.set_running_data(ops=ops_buy_done)
                else:
                    self.set_running_data()
                    self._need_monitor = False
            if not ops_buy_done and ops_sell_done:
                logging.debug("debug: not buy_done and sell_done")
                self.set_running_data()
                self._need_monitor = False

            # Buy, 买入
            if self._trade_direction_cur == LessTradeDirection.LONG:
                logging.debug("debug: trade_direction_cur=long")
                # 检查是否已经买过了，因为程序可能重启过
                # 如果查询数据库里最近一次买的时间大于等于本周期内第一次变成绿柱的时间，则说明已经买过了
                # 如果当前不是第一个绿柱，则找到第一个绿柱
                # 如果当前收盘价格低于第一个绿柱，则是买入好时机，否则不操作
                pos = global_data.get_latest_first_hist_position(long=True)
                first_long_ts = global_data.get_timestamp(pos)
                first_long_price = global_data.get_close(pos)
                ops = ops_buy_done
                if ops:
                    last_buy_done_time = ops[BTC_OPS_TABLE.TIME]
                    if last_buy_done_time:
                        time1 = self.get_time_seconds(first_long_ts)
                        time2 = self.get_time_seconds(last_buy_done_time)
                        if time1 <= time2:
                            # 每个周期只买一次，如果本周期内已经买过了，则不再交易
                            logging.info(
                                "info: Already bought in this period on last_buy_done_tim={0}, first_long_time={1}".format(
                                    last_buy_done_time, first_long_ts))
                            logging.info(
                                "info: BUY_GIVEUP time={0} hist={1} close={2} real_time_close={3} count={4} cost_now={5} "
                                "cost_used={6} cost_average={7} budget_available={8} num_expected={9} "
                                "num_actually={10} num_holding={11}".
                                    format(self._cur_timestamp, self._cur_hist, self._cur_close,
                                           self._real_time_close, self._count, self._cost_now,
                                           self._cost_used, self._cost_average, self._budget_available,
                                           self._num_expected, self._num_actually, self._num_holding))

                            self._trade_direction_his = self._trade_direction_cur
                            self._need_monitor = False
                            self._log_throttle = 0
                            return

                logging.debug("debug: check and try_buy")
                if self._last_price == 0:
                    condition = self._real_time_close < first_long_price
                else:
                    condition = ((self._last_price - self._real_time_close) >= self._add_diff)

                ret = self.try_buy(condition=condition)

                if ret == Operation.BUY_HOLDING:
                    self._need_monitor = True
                else:
                    self._need_monitor = False
                self._log_throttle += 1
            # Sell，卖出
            elif self._trade_direction_cur == LessTradeDirection.SHORT:
                logging.debug("debug: trade_direction_cur=short")
                if self._num_holding > 0.0:
                    # 如果是第一次 buy peak，期待有更大的利润空间，在 peak 之后的第一次由 long -> short 之后卖出
                    if self._count == 1:
                        # 在 MACD 量能为负的时候买入，判断为 peak 买入，则需等待一个周期转换 long -> short 后再卖出。
                        if self._last_hist < 0:
                            first_long_pos = global_data.get_latest_first_hist_position(long=True)
                            first_long_time = global_data.get_timestamp(first_long_pos)
                            first_short_pos = global_data.get_latest_first_hist_position(long=False)
                            first_short_time = global_data.get_timestamp(first_short_pos)
                            # 该条件判断 peak 之后第一次由 long -> short
                            if self.get_time_seconds(self._last_time) < self.get_time_seconds(first_long_time) \
                                    < self.get_time_seconds(first_short_time):
                                logging.info("info: try sell peak position last_time={0}, first_long_time={1}, "
                                             "first_short_time={2}".format(
                                    self._last_time, first_long_time, first_short_time))
                                self.try_sell()
                        # 在 MACD 量能为正的时候买入，为正常趋势变化时的买入，不需要等待一个周期转换时间
                        else:
                            self.try_sell()
                    else:
                        self.try_sell()

                    # 接针
                    logging.debug("debug: last_price={0}, real_time_close={1}, diff={2}, peak_diff={3}".format(
                        self._last_price, self._real_time_close, self._last_price - self._real_time_close,
                        LESS_PEAK_DIFF))
                    if self._last_price - self._real_time_close >= LESS_PEAK_DIFF:
                        logging.info(
                            "info: Add position at peak price real_time_close={0} last_price={1} peak_diff={2}".format(
                                self._real_time_close, self._last_price, LESS_PEAK_DIFF))
                        self.try_buy()
                else:
                    # 接针
                    pos = global_data.get_latest_first_hist_position(long=False)
                    price = global_data.get_close(pos)
                    logging.debug("debug: time={0}, price={1}, real_time_close={2}, diff={3}, peak_diff={4}".format(
                        global_data.get_timestamp(pos), price, self._real_time_close, price - self._real_time_close,
                        LESS_PEAK_DIFF))
                    if price - self._real_time_close >= LESS_PEAK_DIFF:
                        logging.info(
                            "info: Open position at peak price real_time_close={0} last_price={1} peak_diff={2}".format(
                                self._real_time_close, self._last_price, LESS_PEAK_DIFF))
                        self.try_buy()

                self._need_monitor = True
                self._log_throttle += 1

            self._trade_direction_his = self._trade_direction_cur


if __name__ == "__main__":
    lessismore = Lessismore()
    lessismore.init_log()

    logging.info("info: symbol = {0}".format(symbol))
    logging.info("info: interval = {0}".format(interval))
    logging.info("info: cost_now = {0}".format(lessismore._cost_now))
    logging.info("info: max_count = {0}".format(lessismore._max_count))
    logging.info("info: profit_at_least = {0}".format(lessismore._profit_at_least))
    logging.info("info: add_diff = {0}".format(lessismore._add_diff))
    logging.info("info: peak_diff = {0}".format(LESS_PEAK_DIFF))
    logging.info("info: LESSDB_FILE = {0}".format(LESSDB_FILE))

    while True:
        try:
            logging.debug(
                "debug: {0}: run {1}-{2}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                                 symbol, interval))
            lessismore.run()
        except Exception as e:
            logging.error("info: Run exception:" + str(e))

        time.sleep(30)
