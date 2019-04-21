import time

from taObject import TALongByte

# first byte 0x31 or 0xb1
class TAButton(TALongByte):
    @property
    def unit(self):
        return 43

    def tap(self):
        self.press()
        time.sleep(0.2)
        self.lift()

    def press(self):
        self.value = 0x01

    def lift(self):
        self.value = 0x00