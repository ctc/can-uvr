from math import floor

from .Unit import Unit

class TimeUnit(Unit):
    def __init__(self):
        super().__init__(60, "Uhrzeit", "hh:mm", "", 1, False)

    def parseRawValue(self, raw) -> int:
        return int.from_bytes(raw, byteorder='little', signed=False)

    def minutes(self, raw: bytes) -> int:
        return self.parseRawValue(raw) % 60

    def hours(self, raw: bytes) -> int:
        return floor(self.parseRawValue(raw) / 60)

    def stringifyRawValue(self, raw: bytes) -> str:
        return "%02d:%02d" % (self.hours(raw), self.minutes(raw))

    def rawifyString(self, string: str, byte_count: int) -> bytes:
        split = string.split(":")
        value = int(split[0].strip())
        if len(split) > 1:
            value = value * 60 + int(split[1].strip())
        return self.rawifyNumber(value, byte_count)