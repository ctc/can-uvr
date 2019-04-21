import canopen
from threading import Timer
import time, math, struct

OFFSET = 441763200

ONE_DAY = 60 * 60 * 24

TIME_OF_DAY_STRUCT = struct.Struct("<LH")

class TimeProducer:
    timer = None
    interval = 60
    timeAdjustment = -1 * (time.timezone if (time.localtime().tm_isdst == 0) else time.altzone)

    def __init__(self, network: canopen.Network, interval: int):
        self.network = network
        self.interval = interval
        self.timer = Timer(self.interval, self.time)

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.cancel()

    def time(self):
        delta = math.floor(time.time() + self.timeAdjustment) - 441763200

        days, seconds = divmod(delta, ONE_DAY)
        msec = seconds * 1000

        if time.localtime().tm_isdst > 0:
            msec = 0x80000000 | msec

        data = TIME_OF_DAY_STRUCT.pack(int(msec), int(days))

        self.network.send_message(0x100, data)

        print("Produced a time of %i" % delta)

        self.timer = Timer(self.interval, self.time)
        self.timer.start()