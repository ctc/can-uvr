from pydispatch import dispatcher
from threading import Timer
from random import randint
from canopen.sdo.exceptions import SdoError

import devices

class TAObject:
    __idx = None
    __subIdx = None

    _data = None
    __timer = None
    __interval = -1
    _link = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, raw : bytes):
        if self._virtual:
            self._data = raw
        else:
            raise TypeError("Unspported action")

    def __init__(self, device, idx: int, subIdx: int, virtual: bytes=None):
        self.__idx = idx
        self.__subIdx = subIdx
        self.__device = device  # type: devices.TADevice
        self._virtual = virtual is not None
        if virtual:
            self._data = virtual
        else:
            self.reload()

    def __repr__(self):
        return "SDO " + hex(self.__idx) + "[" + hex(self.__subIdx) + "]@" + self.__device.name.value + ": " + self.str_value

    def reload(self):
        if self._virtual or self._link is not None:
            return
        try:
            self._data = self.__device.getSDO(self.idx, self.subIdx)
            dispatcher.send(signal = "UPDATE", sender = self)
        except SdoError:
            #if self.__interval == -1:
            #    self.__timer = Timer(1, self.reload)
            #    self.__timer.start()
            pass
        # Probably some communication exception
        else:
            if self.__interval != -1:
                self.__timer = Timer(self.__interval, self.reload)
                self.__timer.start()

    @property
    def changeable(self):
        return False

    @property
    def device(self):
        return self.__device

    @property
    def idx(self):
        return self.__idx

    @property
    def subIdx(self):
        return self.__subIdx

    @property
    def value(self):
        return None

    @property
    def str_value(self):
        return ""

    def setup_periodic(self, interval = 300, randomize_begin=True):
        if self._virtual or self._link is not None:
            return
        self.__interval = interval
        if randomize_begin:
            interval = randint(5, interval)
        self.__timer = Timer(interval, self.reload)
        self.__timer.start()

    def stop_periodic(self):
        if self.__timer is not None:
            self.__timer.cancel()
        self.__interval = -1

    def update_bytes(self, raw_value):
        pass

    def link(self, output):
        if output is None:
            return
        self.stop_periodic()
        self._link = output
        def on_update():
            self.update_bytes(output.rawValue)
            print("Got update on device %s %s to str value: %s" % (self.device.name.str_value, output.name.str_value, self.str_value))
            dispatcher.send(signal="UPDATE", sender=self)

        print("Linking Ouput #%i on device %s to object at %#x %i" % (output.num, output.device.name.str_value, self.idx, self.subIdx))
        dispatcher.connect(on_update, signal="UPDATE", sender=output, weak=False)