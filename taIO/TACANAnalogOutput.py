from .TACANOutput import TACANOutput

class TACANAnalogOutput(TACANOutput):
    def __init__(self, device, num, unit, rawValue, virtual: bool = False):
        self._baseIdx = 0x2280
        super().__init__(device, num, unit, rawValue, virtual)