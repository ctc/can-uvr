from taObject import TAObject

# first byte 0x1f
class TAString(TAObject):
    @property
    def value(self):
        decoded = self.data[2:].decode('utf-16LE')
        return decoded.rstrip("\u0000")

    @property
    def stringSubIdx(self): # Some byte which is usually the subidx.
        return self.data[1]

    @property
    def str_value(self):
        return self.value