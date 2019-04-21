import devices.TADevice
from functions import InteractFunction, FunctionButton, JalousiePosition
from taObject import TALongInt

class JalousieSteuerung(InteractFunction):
    __hatLamellen = None
    __autobetrieb = None

    def __init__(self, device: devices.TADevice, num: int):
        super().__init__(device, num)
        self.__position = JalousiePosition(self)
        self._init_buttons()
        self.__hatLamellen = self.device.getSDO(0x281c, self.num - 1)[1] == 0x01
        self.__autobetrieb = TALongInt(self.device, 0x2D07, self.num - 1)

    def _init_buttons(self):
        self.__triggerAuto = FunctionButton(self, 0)
        self.__upwards = FunctionButton(self, 1)
        self.__downwards = FunctionButton(self, 2)
        self.__toTop = FunctionButton(self, 3)
        self.__toBottom = FunctionButton(self, 4)
        self.__toHorizontal = FunctionButton(self, 5)
        self._buttons = [self.__triggerAuto, self.__upwards, self.__downwards, self.__toTop, self.__toBottom, self.__toHorizontal]

    @property
    def hatLamellen(self) -> bool:
        if self.__hatLamellen is None:
            self.__hatLamellen = self.device.getSDO(0x281c, self.num - 1)[1] == 0x01
        return self.__hatLamellen

    @property
    def autobetrieb(self):
        if self.__autobetrieb is None:
            self.__autobetrieb = TALongInt(self.device, 0x2D07, self.num - 1)
        return self.__autobetrieb

    @property
    def position(self):
        return self.__position

    def __repr__(self):
        return "Function #%i (%s), %s: %s" % (self.num, self.typ.value, self.name.value, repr(self.position))

    @property
    def triggerAuto(self):
        return self.buttons[0]

    @property
    def upwards(self):
        return self.buttons[1]

    @property
    def downwards(self):
        return self.buttons[2]

    @property
    def toTop(self):
        return self.buttons[3]

    @property
    def toBottom(self):
        return self.buttons[4]

    @property
    def toHorizontal(self):
        return self.buttons[5]