from taObject import TAShortByte
from utils import appendTACheckSum
from units import units
import binascii


# first byte 0x31 or 0xb1
class TALongByte(TAShortByte):
    @property
    def min(self):
        return units[self.unit].parseRawValue(self._data[3])

    @property
    def max(self):
        return units[self.unit].parseRawValue(self._data[4])

    @property
    def changeable(self):
        return self._data[0] & 0x80 == 0x80

    @property
    def value(self):
        if self.unit in units:
            return units[self.unit].parseRawValue(self.rawValue)
        return int.from_bytes(self.rawValue, byteorder='little', signed=False)

    @value.setter
    def value(self, value):
        if self._virtual:
            ba = bytearray(self._data)
            ba[2] = value
            self._data = bytes(ba)
            return
        cmd = appendTACheckSum(self._data[0:1] + int.to_bytes(value, 1, byteorder='little'))
        print("Sending command " + binascii.hexlify(cmd).decode('utf-8'))
        self.device.setSDO(self.idx, self.subIdx, cmd)
        self.reload()