from taObject import TAObject
from units import units

# first byte 0x50
class TALongInt(TAObject):
    @property
    def unit(self):
        return self.data[1]

    @property
    def rawValue(self):
        return self.data[2:4]

    @property
    def value(self):
        if self.unit in units:
            return units[self.unit].parseRawValue(self.rawValue)
        return int.from_bytes(self.rawValue, byteorder='little', signed=False)

    @property
    def str_value(self):
        if self.unit in units:
            return units[self.unit].stringifyRawValue(self.rawValue)
        return self.value

    def update_bytes(self, raw_value):
        bs = bytearray(self.data)
        bs[2] = raw_value[0]
        bs[3] = raw_value[1]
        self._data = bytes(bs)