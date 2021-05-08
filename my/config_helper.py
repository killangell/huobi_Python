from xml.dom.minidom import parse


class ConfigData:
    def __init__(self):
        self.root = None
        self.dom = None
        # account
        self._access_key = None
        self._secret_key = None
        self._account_id = None
        # params
        self._symbol = None
        self._interval = None
        self._base = None
        self._max_count = None
        self._least_profit = None
        self._add_diff = None
        self._peak_diff = None
        self._qds_id = None


class ConfigHelper:
    def __init__(self, file=None):
        self.file = file
        self.root = None

    def init_root(self):
        try:
            self.dom = parse(self.file)
            self.root = self.dom.documentElement
            return True
        except Exception as e:
            return False

    def get_node_value(self, name=None):
        node_list = self.root.getElementsByTagName(name)
        if (len(node_list)) == 0:
            return None
        value = node_list[0].childNodes[0].nodeValue
        return value

    def set_node_value(self, name=None, value=None):
        node_list = self.root.getElementsByTagName(name)
        if (len(node_list)) == 0:
            return False
        node_list[0].childNodes[0].data = value
        return True

    def parse(self, config=ConfigData()):
        config._access_key = self.get_node_value('access_key')
        config._secret_key = self.get_node_value('secret_key')
        config._account_id = self.get_node_value('account_id')
        config._symbol = self.get_node_value('symbol')
        config._interval = self.get_node_value('interval')
        config._base = self.get_node_value('base')
        config._max_count = self.get_node_value('max_count')
        config._least_profit = self.get_node_value('least_profit')
        config._add_diff = self.get_node_value('add_diff')
        config._peak_diff = self.get_node_value('peak_diff')
        config._qds_id = self.get_node_value('qds_id')

    def is_in_list(self, source_list, dst):
        found = False
        for item in source_list:
            if dst == item:
                found = True
                break
        return found

    def check(self, config=ConfigData()):
        symbol_list = ['btcusdt', 'ethusdt', 'filusdt']
        if not self.is_in_list(symbol_list, config._symbol):
            print("Invalid symbol: ", config._symbol)
            return False
        interval_list = ['1min', '5min', '15min', '30min', '60min', '4hour', '1day', '1mon']
        if not self.is_in_list(interval_list, config._interval):
            print("Invalid interval: ", config._interval)
            return False

        return True

    def save(self, config=ConfigData()):
        self.set_node_value('access_key', config._access_key)
        self.set_node_value('secret_key', config._secret_key)
        self.set_node_value('account_id', config._account_id)
        self.set_node_value('symbol', config._symbol)
        self.set_node_value('interval', config._interval)
        self.set_node_value('base', config._base)
        self.set_node_value('max_count', config._max_count)
        self.set_node_value('least_profit', config._least_profit)
        self.set_node_value('add_diff', config._add_diff)
        self.set_node_value('peak_diff', config._peak_diff)
        self.set_node_value('qds_id', config._qds_id)
        with open(self.file, "w", encoding="utf-8") as f:
            self.dom.writexml(f)


if __name__ == "__main__":
    file = 'config.xml'
    config_helper = ConfigHelper(file)
    config = ConfigData()
    ret = config_helper.init_root()
    if ret:
        config_helper.parse(config)
        a = config._access_key
        b = config._secret_key
        c = config._symbol
        d = config._interval
        e = config._base
        f = config._max_count
        g = config._least_profit
        h = config._add_diff
        i = config._peak_diff
        j = config._qds_id
        k = config._account_id
        m = 0
        print(a, b, c, d, e, f, g, h, i, j, k)

        ret = config_helper.check(config)
        print(ret)

        config_to_save = ConfigData()
        config_to_save._access_key = '_access_key'
        config_to_save._secret_key = '_secret_key'
        config_to_save._account_id = '_account_id'
        config_to_save._symbol = '_symbol'
        config_to_save._interval = '_interval'
        config_to_save._base = '_base'
        config_to_save._max_count = '_max_count'
        config_to_save._least_profit = '_least_profit'
        config_to_save._add_diff = '_add_diff'
        config_to_save._peak_diff = '_peak_diff'
        config_to_save._qds_id = '_qds_id'
        config_helper.save(config_to_save)
    else:
        print("error file {0}".format(file))
