import canopen
from threading import Thread
from canopen.sdo.exceptions import SdoError
from pydispatch import dispatcher

from taObject import TAString
from taIO import TACANAnalogOutput, TACANDigitalOutput
from units import units

from . import GenericDevice, VirtualDevice

class TADevice (GenericDevice):
    __state = "Unknown"
    __reads = 0
    __writes = 0
    _uses_vd = None  # type: VirtualDevice
    _used_sdo_client = None  # type: canopen.sdo.SdoClient

    def __init__(self, props, can_network, can_node):
        self._canNode = can_node  # type: canopen.node.RemoteNode
        can_node.sdo.MAX_RETRIES = 3
        can_node.sdo.RESPONSE_TIMEOUT = 1
        ### props must contain the following attributes: "maximum_functions", "type", "physical_input_max", "physical_output_max"
        self.__functions = {}
        super().__init__(props, can_network, can_node.id)

        self._canNetwork.subscribe(0x180 + can_node.id, self.__rxPDOD)
        for i in range(0, 4):
            self._canNetwork.subscribe(0x200 + can_node.id + i * 0x80, self.__rxPDOA(i * 4))
        for i in range(0, 4):
            self._canNetwork.subscribe(0x240 + can_node.id + i * 0x80, self.__rxPDOA(i * 4 + 4 * 4))
        self._canNetwork.subscribe(0x480 + can_node.id, self.__rxMPDO)
        self._canNetwork.subscribe(0x700 + can_node.id, self.__rxNMT)

        self._name = TAString(self, 0x2512, 0x00)

    def use_virtual_device(self, vd: VirtualDevice):
        with self._lock:
            self._uses_vd = vd
            self._used_sdo_client = vd.open_sdo_to(self)

    def unuse_virtual_device(self):
        if self._uses_vd is not None:
            with self._lock:
                self._uses_vd.close_sdo()
                self._uses_vd = None
                self._used_sdo_client = None

    def getSDO(self, idx, sub_idx):
        self.__reads += 1
        with self._lock:
            try:
                if self._uses_vd is not None and self._used_sdo_client is not None:
                    return self._used_sdo_client.upload(idx, sub_idx)
                else:
                    return self._canNode.sdo.upload(idx, sub_idx)
            except SdoError as e:
                print("%s get %#x[%i] raised Exception: %s (retrying...)" % (self.name.value, idx, sub_idx, repr(e)))
                try:
                    if self._uses_vd is not None and self._used_sdo_client is not None:
                        return self._used_sdo_client.upload(idx, sub_idx)
                    else:
                        return self._canNode.sdo.upload(idx, sub_idx)
                except SdoError as e:
                    print("%s get %#x[%i] raised Exception: %s (was 2nd try)" % (self.name.value, idx, sub_idx, repr(e)))
                    raise

    def setSDO(self, idx, sub_idx, data):
        self.__writes += 1
        with self._lock:
            try:
                if self._uses_vd is not None and self._used_sdo_client is not None:
                    self._used_sdo_client.download(idx, sub_idx, data, True) # TA Devices does not support expedited transfer
                else:
                    self._canNode.sdo.download(idx, sub_idx, data, True) # TA Devices does not support expedited transfer
            except SdoError as e:
                print("%s set %#x[%i] raised Exception: %s (retrying...)" % (self.name.value, idx, sub_idx, repr(e)))
                try:
                    if self._uses_vd is not None and self._used_sdo_client is not None:
                        self._used_sdo_client.download(idx, sub_idx, data, True) # TA Devices does not support expedited transfer
                    else:
                        self._canNode.sdo.download(idx, sub_idx, data, True) # TA Devices does not support expedited transfer
                except SdoError as e:
                    print("%s set %#x[%i] raised Exception: %s (was 2nd try)" % (self.name.value, idx, sub_idx, repr(e)))
                    raise

    def __rxNMT(self, can_id, data, timestamp):
        state = data[0]
        if state == 0x00:
            self.__state = "Booting"
        elif state == 0x04:
            self.__state = "Stopped"
        elif state == 0x05:
            self.__state = "Operational"
        elif state == 0x80:
            self.__state = "Pre-operational"
        else:
            self.__state = "Unknown"

        Thread(target = dispatcher.send, kwargs = {"signal": "NMT", "sender": self}).start()

    def __rxPDOA(self, offset): # When the TA device sends out a mpdo
        def callback(can_id, data, timestamp):
            def target():
                for idx in range(0, 4):
                    num = offset + idx + 1
                    byte_val = data[idx*2 : (idx + 1) * 2]
                    if num in self._canAnalogOutputs:
                        output = self._canAnalogOutputs[num]
                        output.update(byte_val)
                    #elif byte_val != b'\x00\x00\x00\x00':
                        #pass # Think of some solution to add it
            Thread(target=target).start()

        return callback

    def __rxPDOD(self, can_id, data, timestamp): # When the TA device sends out a mpdo
        def target():
            raw = int.from_bytes(data[0:4], signed=False, byteorder='little') # Shall be 0x4E00

            for idx in range(1, 33):
                val = raw & 0x01
                byte_val = val.to_bytes(2, byteorder='little', signed=False)
                if idx in self._canDigitalOutputs:
                    output = self._canDigitalOutputs[idx]
                    output.update(byte_val)
                elif val == 0x01:
                    self._canDigitalOutputs[idx] = TACANDigitalOutput(self, idx, byte_val)
                    dispatcher.send(num = idx, signal = "ADD_CAN-DIGITAL-OUTPUT", sender = self)

                raw = raw >> 1

        Thread(target=target).start()

    def __rxMPDO(self, can_id, data, timestamp): # When the TA device sends out a mpdo
        def target():
            if data[0] >> 7: # DAM MPDO
                return
            if can_id - 0x480 != data[0]:
                return

            idx = int.from_bytes(data[1:3], signed=False, byteorder='little') # Shall be 0x4E00
            subIdx = data[3] # x: 1-32: Analog x, 33-64: Digital x - 32
            unit = data[7] # Unit
            unitObj = units[unit]
            rawValue = data[4:6]

            if idx != 0x4E00:
                return
            if subIdx == 0 or subIdx > 64:
                return

            if subIdx <= 32:
                if subIdx in self._canAnalogOutputs:
                    output = self._canAnalogOutputs[subIdx]
                    output.update(rawValue)
                else:
                    self._canAnalogOutputs[subIdx] = TACANAnalogOutput(self, subIdx, unitObj, rawValue)
                    dispatcher.send(num = subIdx, signal = "ADD_CAN-ANALOG-OUTPUT", sender = self)
            elif 33 <= subIdx <= 64:
                input_num = subIdx - 32
                if input_num in self._canDigitalOutputs:
                    output = self._canDigitalOutputs[input_num]
                    output.update(rawValue)
                else:
                    self._canDigitalOutputs[input_num] = TACANDigitalOutput(self, input_num, rawValue)
                    dispatcher.send(num = input_num, signal = "ADD_CAN-DIGITAL-OUTPUT", sender = self)

        Thread(target=target).start()

    @property
    def state(self):
        return self.__state

    def reloadCanOutputs(self):
                 # DAM  NodeId
        mpdoid = (0x80 + self.id).to_bytes(1, byteorder='little', signed=False)
                 # Sending MPDO to mpdoid, idx 0x4E01, subidx = 0x01, data = 0x00 0x00 0x00 0x01
        self._canNetwork.send_message(0x480, mpdoid + b'\x01\x4e\x01\x01\x00\x00\x00')

    def scanFunctions(self):
        from functions import BasicFunction, JalousieSteuerung
        for i in range(0x00, self.maximum_functions - 1):
            funType = self.getSDO(0x4800, i)[1]
            if funType == 0x00:
                if i + 1 in self.__functions:
                    del self.__functions[i + 1] #TODO: Notify of deletion
                break
            elif funType == 0x28:
                self.__functions[i + 1] = JalousieSteuerung(self, i + 1)
                dispatcher.send(num = i + 1, signal = "ADD_FUNCTION", sender = self)
            else:
                self.__functions[i + 1] = BasicFunction(self, i + 1)
                dispatcher.send(num = i + 1, signal = "ADD_FUNCTION", sender = self)
        return self.__functions

    @property
    def functions(self):
        if self.__functions is None:
            return self.scanFunctions()
        return self.__functions

    @property
    def maximum_functions(self):
        return self._props['maximum_functions']

    @property
    def physical_input_max(self):
        return self._props['physical_input_max']

    @property
    def physical_output_max(self):
        return self._props['physical_output_max']

    @property
    def reads(self):
        return self.__reads

    @property
    def writes(self):
        return self.__writes