from .TACANOutput import TACANOutput
from units import units

class TACANDigitalOutput(TACANOutput):
    def __init__(self, device, num, rawValue, virtual: bool = False):
        self._baseIdx = 0x2380
        super().__init__(device, num, units[43], rawValue, virtual)

    def __repr__(self):
        return "CAN Output #%i (Digital), %s: %s"  % (self.num, self.name.value, self.str_value)