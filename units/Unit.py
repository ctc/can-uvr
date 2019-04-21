class Unit:
    def __init__(self, unit_id: int, unit_name: str, object_name: str, suffix: str, multiplicator: float, signed: bool):
        self.__unitId = unit_id
        self.__unitName = unit_name
        self.__objectName = object_name
        self.__suffix = suffix
        self.__multiplicator = multiplicator
        self.__signed = signed

    @property
    def unitId(self) -> int:
        return self.__unitId

    @property
    def unitName(self) -> str:
        return self.__unitName

    @property
    def objectName(self) -> str:
        return self.__objectName

    @property
    def suffix(self) -> str:
        return self.__suffix

    @property
    def multiplicator(self) -> float:
        return self.__multiplicator

    @property
    def signed(self) -> bool:
        return self.__signed

    def parseRawValue(self, raw) -> float:
        return round(int.from_bytes(raw, byteorder='little', signed=self.__signed) * self.__multiplicator, 5)

    def stringifyRawValue(self, raw) -> str:
        return str(self.parseRawValue(raw)) + " " + self.__suffix

    def rawifyNumber(self, num: float, byte_count: int) -> bytes:
        return int(num / self.__multiplicator).to_bytes(byte_count, byteorder='little', signed=self.__signed)

    def rawifyString(self, string: str, byte_count: int) -> bytes:
        return self.rawifyNumber(float(string.replace(self.__suffix, "").strip()), byte_count)