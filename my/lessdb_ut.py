from lessismore import LESSDB_FILE
from lessdb import Lessdb

from my.lessdb import Operation

if __name__ == "__main__":
    print("database name: " + LESSDB_FILE)
    lessdb = Lessdb(LESSDB_FILE)
    # lessdb.update_by_operation()
    lessdb.debug_select_all()
    # lessdb.debug_select_all()
    # LESSDB_FILE_TEST = 'less_test.db'
    # lessdb = Lessdb(LESSDB_FILE_TEST)

    # values = ['20210519_190000', 0, -241.42737732970397, 38790.73, 9, 30.0, 432.78, 45081, 0, 0.0012897894048357682, 0.0, 0.0096]
    # lessdb.insert('BTC_OPS', values)
    # print("after fix")
    # lessdb.debug_select_all()

    #
    # lessdb.select('BTC_OPS')
    #
    # ret = lessdb.select_last_one()
    # operation = ret[2]
    # time = ret[1]
    #
    # lessdb.select_last_one_by_operation(operation=Operation.BUY_DONE)

# D:\Work\huobi_Python\huobi_Python\my>"D:\Tools\sqlite-tools-win32-x86-3350300\sqlite3.exe" less.db
# SQLite version 3.35.3 2021-03-26 12:12:52
# Enter ".help" for usage hints.
# sqlite> .table
# BTC_OPS
# sqlite>