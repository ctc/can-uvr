from .Unit import Unit

class RaffstoreUnit(Unit):
    def __init__(self):
        super().__init__(55, "Raffstore Position", "Raffstore", "", 1, False)

    def parseRawValue(self, raw: bytes) -> str:
        lamelle = raw[1]
        jalousie = raw[0]
        return str(jalousie) + "|" + str(lamelle)

    def lamelle(self, raw: bytes) -> int:
        return raw[1]

    def jalousie(self, raw: bytes) -> int:
        return raw[0]

    def lamelleProzent(self, raw: bytes) -> str:
        return str(raw[1]) + "%"

    def jalousieProzent(self, raw: bytes) -> str:
        return str(raw[0]) + "%"

    def stringifyRawValue(self, raw: bytes) -> str:
        return self.jalousieProzent(raw) + " " + self.lamelleProzent(raw)

    def rawifyNumber(self, num: float, byte_count: int) -> bytes:
        raise TypeError("RaffstoreUnit is special!")

    def rawifyString(self, string: str, byte_count: int) -> bytes:
        return self.rawifyNumber(float(string.replace(self.__suffix, "").strip()), byte_count)