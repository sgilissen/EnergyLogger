import time
import threading


def read_sun2k():
    t = threading.currentThread()
    while getattr(t, "do_run", True):
        print('Reading SUN2000')
        time.sleep(1)
    print("Stopped SUN2k reading thread")