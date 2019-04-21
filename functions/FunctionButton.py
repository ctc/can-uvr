import functions.BasicFunction
from taObject import TAString, TAButton

class FunctionButton:
    def __init__(self, function: functions.BasicFunction, button_num: int):
        self.__function = function
        self.__buttonNum = button_num
        self.__name = TAString(function.device, 0x3F00 + button_num, function.num - 1)
        self.__long = TAButton(function.device, 0x4F00 + button_num, function.num - 1)

    def tap(self):
        self.__long.tap()

    def name(self):
        return self.__name

    def press(self):
        return self.__long.press()

    def lift(self):
        return self.__long.lift()