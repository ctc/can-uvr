class BasicFunction:
    __name = None
    __typ = None
    __num = None
    __device = None

    def __init__(self, device, num: int):
        """

        :type device: devices.TADevice.TADevice
        """
        self.__device = device
        self.__num = num

    @property
    def num(self):
        return self.__num

    @property
    def name(self):
        if self.__name is None:
            self.__name = TAString(self.__device, 0x280F, self.__num - 1)
        return self.__name

    @property
    def typ(self):
        if self.__typ is None:
            self.__typ = TAString(self.__device, 0x2800, self.__num - 1)
        return self.__typ

    @property
    def device(self):
        return self.__device

    def __repr__(self):
        return "Function #%i (%s), %s" % (self.num, self.typ.value, self.name.value)

from taObject import TAString