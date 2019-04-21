import time
from pydispatch import dispatcher

from .TACANObject import TACANObject
from taObject import TAStringPtr

class TACANOutput(TACANObject):
    def __init__(self, device, num, unit, rawValue, virtual: bool = False):
        self.__rawValue = self.__last_change = self.__last_update = None
        super().__init__(device, num, unit, virtual)
        self.update(rawValue)
        if not virtual:
            self._source_type = TAStringPtr(self.device, self.baseIdx + 0x2000 + 0x50, self.num - 1)
            self._source_object = TAStringPtr(self.device, self.baseIdx + 0x2000 + 0x51, self.num - 1)
            self._source_variable = TAStringPtr(self.device, self.baseIdx + 0x2000 + 0x52, self.num - 1)


    @property
    def rawValue(self):
        return self.__rawValue

    #def reloadFromSDO(self):
    #    self.update(self.device.getSDO(self.baseIdx + 0x55, self.num - 1)[2:4])

    def update(self, raw_value):
        if self.__rawValue != raw_value:
            self.__last_change = time.time()
        self.__last_update = time.time()
        self.__rawValue = raw_value
        dispatcher.send(signal = "UPDATE", sender = self)

    def update_from_float(self, new: float):
        if self.unit is not None:
            bs = self.unit.rawifyNumber(new, 2)
            self.update(bs)
        else:
            self.update(int(new).to_bytes(length= 2, byteorder='little', signed=False))

    def update_from_string(self, new: str):
        if self.unit is not None:
            self.update(self.unit.rawifyString(new, 2))
        else:
            raise TypeError("No unit specified!")

    @property
    def last_update(self):
        return self.__last_update

    @property
    def last_change(self):
        return self.__last_change

    @property
    def value(self):
        if self.unit is not None:
            return self.unit.parseRawValue(self.rawValue)
        return int.from_bytes(self.rawValue, byteorder='little', signed=False)

    @property
    def str_value(self):
        if self.unit is not None:
            return self.unit.stringifyRawValue(self.rawValue)
        return self.value

    def __repr__(self):
        return "CAN Output #%i (%s), %s: %s"  % (self.num, self.unit.unitName, self.name.value, self.str_value)

    @property
    def source_type(self):
        if self._virtual:
            return None
        if self._source_type is None:
            self._source_type = TAStringPtr(self.device, self.baseIdx + 0x2000 + 0x50, self.num - 1)
        return self._source_type

    @property
    def source_object(self):
        if self._virtual:
            return None
        if self._source_object is None:
            self._source_object = TAStringPtr(self.device, self.baseIdx + 0x2000 + 0x51, self.num - 1)
        return self._source_object

    @property
    def source_variable(self):
        if self._virtual:
            return None
        if self._source_variable is None:
            self._source_variable = TAStringPtr(self.device, self.baseIdx + 0x2000 + 0x52, self.num - 1)
        return self._source_variable

    def check_link_variable(self):
        from devices import TADevice
        from functions import JalousieSteuerung
        device = self.device  # type: TADevice
        var = None
        if not isinstance(self.device, TADevice):
            return
        if self.source_type.ptr_idx == 0x5649 and self.source_type.ptr_sub_idx == 0x03:
            # Functions
            if self.source_object.ptr_idx == 0x55e3:
                if self.source_object.ptr_sub_idx + 1 not in device.functions:
                    return
                func = device.functions[self.source_object.ptr_sub_idx + 1]
                if isinstance(func, JalousieSteuerung) and self.source_variable.ptr_idx == 0x5176:
                    if self.source_variable.ptr_sub_idx == 0x01:  # Sollposition
                        var = func.position.sollPosition
                    elif self.source_variable.ptr_sub_idx == 0x02:  # Istposition
                        var = func.position.istPosition

        if var is not None:
            var.link(self)