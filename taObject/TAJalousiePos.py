from taObject import TALongInt
from units import units

raffstoreUnit = units[0x37]

# first bytes are 0x50 0x37
class TAJalousiePos(TALongInt):
    @property
    def value(self):
        return raffstoreUnit.stringifyRawValue(self.rawValue)

    def lamelle(self):
        return raffstoreUnit.lamelle(self.rawValue)

    def jalousie(self):
        return raffstoreUnit.jalousie(self.rawValue)

    def lamelleProzent(self):
        return raffstoreUnit.lamelleProzent(self.rawValue)

    def jalousieProzent(self):
        return raffstoreUnit.jalousieProzent(self.rawValue)