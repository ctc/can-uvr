from typing import Tuple
from .Unit import Unit

class DigitalUnit(Unit):
    def __init__(self, unit_id: int, unit_name: str, object_name: str, table: Tuple):
        super().__init__(unit_id, unit_name, object_name, "", 1, False)
        self.__array = table

    def parseRawValue(self, raw: bytes) -> int:
        ret = super().parseRawValue(raw)
        if ret < 0:
            return 0
        if ret >= len(self.__array):
            return len(self.__array) - 1
        return ret

    def stringifyRawValue(self, raw: bytes) -> str:
        return self.__array[self.parseRawValue(raw)]

    def rawifyNumber(self, num: float, byte_count: int) -> bytes:
        return max(0, min(len(self.__array) - 1, int(num))) .to_bytes(byte_count, byteorder='little', signed=False)

    def rawifyString(self, string: str, byte_count: int) -> bytes:
        string = string.strip()
        for k in range(len(self.__array)):
            if self.__array[k].lower() == string.lower():
                return self.rawifyNumber(k, byte_count)
        try:
            return self.rawifyNumber(int(string), byte_count)
        except ValueError:
            return self.rawifyNumber(0, byte_count)