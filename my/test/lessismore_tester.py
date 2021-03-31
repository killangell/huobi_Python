import time
import logging

from my.organized import Organized
from my.upath import UPath
from huobi.client.market import MarketClient
from huobi.constant import *
from huobi.utils import *
import pandas as pd

market_client = MarketClient(init_log=True)
interval = CandlestickInterval.MIN5
symbol = "btcusdt"
kline_num = 2000
smart_holding = True
money_available = 350
money_budget_each = 20
log_file = "{0}_{1}_{2}_{3}_[{4}-{5}].log".format(symbol, interval, kline_num,
                                                  'holding' if smart_holding else 'non-holding',
                                                  money_available, money_budget_each)

# log_file = "lessismore_tester.log"
# log_backup_file = "lessismore_tester.log.backup"

class Lessismore:
    def __init__(self):
        pass

    def init_log(self):
        # backup a log copy, in case any error would be overwritten in a new run
        # if UPath.is_file_exists(log_backup_file):
        #     UPath.remove(log_backup_file)
        #
        # if UPath.is_file_exists(log_file):
        #     UPath.rename(log_file, log_backup_file)

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

    def run(self):
        kline_list = market_client.get_candlestick(symbol, interval, kline_num)
        # LogInfo.output("---- {interval} candlestick for {symbol} ----".format(interval=interval, symbol=symbol))
        # LogInfo.output_list(kline_list)

        global_data = Organized()
        global_data = self.parse_kline_data(kline_list)
        global_data.calculate_macd()

        global money_available
        global money_budget_each
        bought_count = 0
        bought_used_money = 0
        bought_num = 0
        last_price = 0
        averange_price = 0
        macd_hist_his = None
        macd_hist_cur = None
        profit_at_least = 200


        global_data.calculate_macd()

        i = 0
        while pd.isnull(global_data.get_hist(i)):
            i += 1
            continue

        for i in range(i, global_data.get_len()):
            if global_data.get_hist(i) > 0:
                macd_hist_cur = True
            else:
                macd_hist_cur = False

            if macd_hist_his != macd_hist_cur:

                # 执行 buy
                if macd_hist_cur:
                    if money_available > money_budget_each:
                        unholding_condition = global_data.get_close(i) < last_price
                        if not smart_holding:
                            unholding_condition = True
                        if last_price == 0 or (last_price > 0 and unholding_condition):
                            bought_count += 1
                            money_available -= money_budget_each
                            bought_num_this_time = money_budget_each / global_data.get_close(i)
                            bought_num += bought_num_this_time
                            bought_used_money += money_budget_each
                            averange_price = bought_used_money / bought_num
                            last_price = global_data.get_close(i)
                            logging.info(
                                "buy time={0} macd={1} close={2} bought_count={3} bought_money={4} bought_num={5} money_available={6} averange_price={7}".
                                    format(global_data.get_timestamp(i), macd_hist_cur, global_data.get_close(i),
                                           bought_count,
                                           bought_used_money, bought_num, money_available, averange_price))
                        else:
                            logging.info(
                                "buy holding time={0} macd={1} close={2} bought_count={3} bought_money={4} bought_num={5} money_available={6} averange_price={7}".
                                    format(global_data.get_timestamp(i), macd_hist_cur, global_data.get_close(i),
                                           bought_count,
                                           bought_used_money, bought_num, money_available, averange_price))

                    else:
                        logging.error(
                            "buy error time={0} macd={1} close={2} bought_count={3} bought_money={4} bought_num={5} money_available={6}".
                                format(global_data.get_timestamp(i), macd_hist_cur, global_data.get_close(i),
                                       bought_count,
                                       bought_used_money, bought_num, money_available))
                    macd_hist_his = True

                # 执行 sell
                else:
                    if not macd_hist_his:
                        continue

                    profit = 0
                    # 有利润才 sell
                    if global_data.get_close(i) - profit_at_least > averange_price:
                        sell_money = global_data.get_close(i) * bought_num
                        money_available += sell_money
                        profit = sell_money - bought_used_money
                        bought_count = 0
                        bought_used_money = 0
                        bought_num = 0
                        averange_price = 0
                        last_price = 0

                        logging.info("sell time={0} macd={1} close={2} profit={3} money_available={4}".format(
                            global_data.get_timestamp(i), macd_hist_cur,
                            global_data.get_close(i), profit, money_available))
                    else:
                        logging.error("sell holding time={0} macd={1} close={2} profit={3} money_available={4}".format(
                            global_data.get_timestamp(i), macd_hist_cur,
                            global_data.get_close(i), profit, money_available))

                macd_hist_his = macd_hist_cur


if __name__ == "__main__":
    lessismore = Lessismore()
    lessismore.init_log()
    lessismore.run()