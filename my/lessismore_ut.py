from my.lessismore import Lessismore

if __name__ == "__main__":
    lessismore = Lessismore()
    seconds = lessismore.get_time_seconds("20120304_122334")
    print(seconds)