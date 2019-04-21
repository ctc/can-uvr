from taObject import TAJalousiePos, TALongByte

class JalousiePosition:
    __sollPos = None
    __istPos = None
    __manualHeight = None
    __manualTilt = None
    def __init__(self, function):
        self.__function = function  # type: functions.JalousieSteuerung
        self.__sollPos = TAJalousiePos(self.__function.device, 0x2d03, self.__function.num - 1)
        self.__istPos = TAJalousiePos(self.__function.device, 0x2d05, self.__function.num - 1)

    @property
    def sollPosition(self):
        if self.__sollPos is None:
            self.__sollPos = TAJalousiePos(self.__function.device, 0x2d03, self.__function.num - 1)
        return self.__sollPos

    @property
    def istPosition(self):
        if self.__istPos is None:
            self.__istPos = TAJalousiePos(self.__function.device, 0x2d05, self.__function.num - 1)
        return self.__istPos

    def reload(self):
        self.sollPosition.reload()
        self.istPosition.reload()

    def set(self, height: int, tilt: int):
        if self.__manualHeight is None:
            self.__manualHeight = TALongByte(self.__function.device, 0x4818, self.__function.num - 1)
        if self.__manualTilt is None:
            self.__manualTilt = TALongByte(self.__function.device, 0x4819, self.__function.num - 1)
        if 0 <= height <= 100 and 0 <= tilt <= 100:
            self.__manualHeight.value = height
            self.__manualTilt.value = tilt

    def __repr__(self):
        return "Soll: " + repr(self.sollPosition) + " Ist: " + repr(self.istPosition)