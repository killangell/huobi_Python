import sqlite3
from enum import IntEnum
from my.upath import UPath


class Operation(IntEnum):
    BUY_DONE = 0,
    BUY_HOLDING = 1,
    BUY_ERROR = 2,
    SELL_DONE = 3,
    SELL_HOLDING = 4


class BTC_OPS_TABLE(IntEnum):
    ID = 0,
    TIME = 1,
    OPERATION = 2,
    HIST = 3,  # MACD 柱状线, real
    CLOSE = 4,  # 收盘价格, real
    COUNT = 5,  # 操作次数, real
    COST_NOW = 6,  # 当次成本, real
    COST_USED = 7,  # 已开销成本, real
    COST_AVERAGE = 8,  # 平均成本, update
    BUDGET_AVAILABLE = 9,  # 所剩预算, update
    NUM_EXPECTED = 10,  # 预期买到的数量, real
    NUM_ACTUALLY = 11,  # 实际到账的数量, update
    NUM_HOLDING = 12,  # 账户持有的总数量, update


class Lessdb:
    def __init__(self, dbfile=None):
        self._lessdb_file = dbfile
        if not UPath.is_file_exists(self._lessdb_file):
            # 数据库不存在，则创建数据库
            conn = sqlite3.connect(self._lessdb_file)
            cur = conn.cursor()
            # 创建表格
            sql_create_table_qps = '''CREATE TABLE BTC_OPS
                               (id              INTEGER PRIMARY KEY,
                               time             TEXT    NOT NULL,
                               operation        int     NOT NULL,
                               hist             float     NOT NULL,
                               close            float,
                               count            int,
                               cost_now         float,
                               cost_used        float,
                               cost_average     float,
                               budget_available float,
                               num_expected     float,
                               num_actually     float,
                               num_holding      float)'''
            # 执行sql语句
            cur.execute(sql_create_table_qps)
            conn.commit()

            cur.close()
            conn.close()

    def insert(self, table='BTC_OPS', values=None):
        conn = sqlite3.connect(self._lessdb_file)
        cur = conn.cursor()

        cur.execute(
            'INSERT INTO {0} (time, operation, hist, close, count, cost_now, cost_used, cost_average, budget_available, num_expected, num_actually, num_holding) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'.format(table), values)
        conn.commit()

        cur.close()
        conn.close()

    def select(self, table='BTC_OPS'):
        conn = sqlite3.connect(self._lessdb_file)
        cur = conn.cursor()

        cur.execute("SELECT * FROM {0}".format(table))
        # 获取查询结果
        ret = cur.fetchall()
        for row in ret:
            print(row)

        cur.close()
        conn.close()

        return ret

    def select_last_one(self, table='BTC_OPS'):
        conn = sqlite3.connect(self._lessdb_file)
        cur = conn.cursor()

        cur.execute("SELECT * FROM {0} ORDER BY ID DESC LIMIT 1".format(table))
        # 获取查询结果
        ret = cur.fetchall()
        for row in ret:
            print(row)

        cur.close()
        conn.close()

        if ret:
            return ret[0]
        else:
            return None

    def select_last_one_by_operation(self, table='BTC_OPS', operation=Operation.BUY_DONE):
        conn = sqlite3.connect(self._lessdb_file)
        cur = conn.cursor()

        cur.execute("SELECT * FROM {0} WHERE operation={1} ORDER BY ID DESC LIMIT 1".format(table, operation))
        # 获取查询结果
        ret = cur.fetchall()
        for row in ret:
            print(row)

        cur.close()
        conn.close()

        if ret:
            return ret[0]
        else:
            return None

    def debug_select_all(self, table='BTC_OPS'):
        conn = sqlite3.connect(self._lessdb_file)
        cur = conn.cursor()

        cur.execute("SELECT * FROM {0} ORDER BY ID DESC".format(table))
        # 获取查询结果
        ret = cur.fetchall()
        for row in ret:
            print(row)

        cur.close()
        conn.close()

    def update_by_operation(self, table='BTC_OPS', operation=Operation.BUY_DONE, cost_used=400, cost_average=55430):
        conn = sqlite3.connect(self._lessdb_file)
        cur = conn.cursor()

        cur.execute("SELECT * FROM {0} WHERE operation={1} ORDER BY ID DESC LIMIT 1".format(table, operation))
        # 获取查询结果

        ret = cur.fetchall()
        for row in ret:
            print(row)
        id = ret[0][BTC_OPS_TABLE.ID]
        print(id)

        cur.execute(
            "UPDATE {0} SET cost_used={1}, cost_average={2}, operation={3} WHERE id={4}".format(table, cost_used,
                                                                                                cost_average,
                                                                                                Operation.BUY_DONE, id))
        conn.commit()

        cur.close()
        conn.close()

        if ret:
            return ret[0]
        else:
            return None



