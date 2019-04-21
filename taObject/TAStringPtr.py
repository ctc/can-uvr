from taObject import TAObject

# first byte 0x11 or 0x12
class TAStringPtr(TAObject):
    @property
    def ptr_idx(self):
        return int.from_bytes(self.data[3:5], byteorder='little', signed=False)

    @property
    def ptr_sub_idx(self):
        return self.data[1]

    @property
    def max_sub_idx(self):
        return self.data[2] - 1

    @property
    def value(self):
        return "%#x[%#x]" % (self.ptr_idx, self.ptr_sub_idx)

    @property
    def str_value(self):
        return self.value