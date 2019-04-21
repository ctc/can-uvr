from taObject import TAString
from units import Unit
import devices.GenericDevice

class TAIOObject:
    __name = None

    def __init__(self, device, num, unit, virtual: bool = False):
        self._baseIdx = self._baseIdx or 0x0000
        self.__device = device  # type: devices.GenericDevice
        self.__num = num
        self.__unit = unit  # type: Unit
        self._virtual = virtual
        if virtual:
            self.__name = TAString(device, self.baseIdx + 0xf, self.num - 1, b'\x1f' + (self.num - 1).to_bytes(1, byteorder='little', signed=False) + ("Virtual TAIO #%i" % self.num).encode('utf-16le'))

    # Needs to be updated by subclass
    @property
    def baseIdx(self):
        return self._baseIdx

    @property
    def num(self):
        return self.__num

    @property
    def device(self):
        return self.__device

    @property
    def name(self):
        if self.__name is None:
            self.__name = TAString(self.device, self.baseIdx + 0xf, self.num - 1)
        return self.__name

    @property
    def unit(self):
        return self.__unit

    def __repr__(self):
        return "Generic IO #%i (%s), %s"  % (self.num, self.unit.unitName, self.name.value)