class Utils:
    """
    Get the difference of an arithmetic sequence
    获得等差数列的差值
    Sn=n(a1+an)/2
    Sn=na1+n(n-1)d/2
    """
    @staticmethod
    def get_diff_of_arit_seq(a1=20, n=10, sn=210):
        if (a1 * n) > sn:
            return 0
        d = (2 * (sn - n * a1)) / (n * (n - 1))
        return d

    """
    获取等差数列
    """
    @staticmethod
    def get_list_of_arit_seq(a1=20, n=10, sn=210):
        d = Utils.get_diff_of_arit_seq(a1, n, sn)
        ret = []
        if d > 0:
            for i in range(0, n):
                ret.append(a1 + i * d)
        return ret

    """
    精确到小数点后多少位
    """
    @staticmethod
    def precision_x(str='0.123456789', precision=6):
        if str == '0' or str == 0:
            return 0
        if str.count('.') == 0:
            return str
        s1 = str
        s1_list = s1.split('.')
        s1_new = s1_list[0] + '.' + s1_list[1][:precision]
        return s1_new


if __name__ == "__main__":
    print(Utils.get_diff_of_arit_seq(15, 10, 210))
    print(Utils.get_diff_of_arit_seq(10, 10, 200))
    print(Utils.get_diff_of_arit_seq(30, 10, 400))

    str = "{0}".format(Utils.get_diff_of_arit_seq(30, 10, 400))
    print(Utils.precision_x(str, 2))
    print(Utils.precision_x("20", 2))
    print(Utils.precision_x("20.0", 4))

    list = Utils.get_list_of_arit_seq(30, 10, 426)
    print(list)
    sn = 0
    for i in range(0, len(list)):
        sn += list[i]
        print(sn)

    list = Utils.get_list_of_arit_seq(25, 10, 436)
    print(list)
    sn = 0
    for i in range(0, len(list)):
        sn += list[i]
        print(sn)

    print("3")
    list = [30.0, 32.95066666666667, 35.90133333333333, 38.852000000000004, 41.80266666666667, 44.75333333333334, 47.70400000000001, 50.65466666666667, 53.605333333333334, 56.556000000000004]
    print(list)
    sn = 0
    for i in range(0, len(list)):
        sn += list[i]
        print(sn)