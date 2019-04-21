import threading, binascii
from canopen import Network, ObjectDictionary
from canopen.objectdictionary import Variable
from canopen.sdo import SdoClient, SdoServer
from pydispatch import dispatcher
import time

from taObject import TAString
from taIO import TACANDigitalOutput, TACANAnalogOutput
from . import GenericDevice
from units import Unit
from utils import TAODVariable

cob_ids = {
     1: 0x200,
     5: 0x280,
     9: 0x300,
    13: 0x380,
    17: 0x240,
    21: 0x2C0,
    25: 0x340,
    29: 0x3C0
}

class VirtualDevice(GenericDevice):
    _od = None  # type: ObjectDictionary
    _name = None  # type: TAString
    __analog_interval = 30  # type: int
    __digital_interval = 30  # type: int

    _nmt_timer = None  # type: threading.Timer
    _eh_timer = None  # type: threading.Timer

    def __init__(self, props, can_network: Network, can_node_id: int):
        ### props must contain the following attributes: "type", "name"
        self._name = TAString(self, 0x2512, 0x00, b'\x1F\x00' + props["name"].encode("utf-16le"))
        self.__init_od()

        self._local_node = can_network.create_node(can_node_id, self._od)
        self._sdo_servers = {}

        super().__init__(props, can_network, can_node_id)

        self._sdo_client = SdoClient(0x640 + can_node_id, 0x5C0 + can_node_id, ObjectDictionary())

        self._sdo_client.network = can_network
        can_network.subscribe(0x5C0 + can_node_id, self._sdo_client.on_response)

        self._sdo_node = None

        self.__analog_timer = threading.Timer(self.__analog_interval, self.__send_analog)
        self.__digital_timer = threading.Timer(self.__digital_interval, self.__send_digital)
        self.__analog_timer.start()
        self.__digital_timer.start()
        for i in range(0x400, 0x440):
            self._canNetwork.subscribe(i, self.__cs_mpdo_callback)
        for i in range(0x480, 0x4C0):
            self._canNetwork.subscribe(i, self.__dl_eh_mpdo_callback)

        self._nmt_send()
        self._eh_timer = threading.Timer(10, self._eh_send)
        self._eh_timer.start()

    def stop(self):
        self._eh_timer.cancel()
        self._nmt_timer.cancel()
        self.__analog_timer.cancel()
        self.__digital_timer.cancel()

    def __init_od(self):
        self._od = ObjectDictionary()

        type = Variable("Device type", 0x23E2, 0x01)
        type.access_type = "const"
        type.value = b"\x8A\x00\x00\x00"
        self._od.add_object(type)

        name = Variable("Device name", 0x1008, 0x00)
        name.access_type = "const"
        name.value = self.name.value.encode('ascii')
        self._od.add_object(name)

        self._od.add_object(TAODVariable(self._name, name="Device name"))

    def _eh_send(self):
        for i in range(0x00, 0x06):
            offset = i * 6 + 1
            cmd = b'\x01' + i.to_bytes(length=1, byteorder='little', signed=False)
            for j in range(offset, offset + 6):
                if j in self._canAnalogOutputs:
                    cmd = cmd + self.canAnalogOutputs[j].unit.unitId.to_bytes(length=1, byteorder='little', signed=False)
                else:
                    cmd = cmd + b'\x00'
            self._canNetwork.send_message(0x1C0 + self.id, cmd)

        for i in range(0x00, 0x06):
            offset = i * 6 + 1
            cmd = b'\x01' + (0x06 + i).to_bytes(length=1, byteorder='little', signed=False)
            for j in range(offset, offset + 6):
                if j in self.canDigitalOutputs:
                    cmd = cmd + self.canDigitalOutputs[j].unit.unitId.to_bytes(length=1, byteorder='little',
                                                                               signed=False)
                else:
                    cmd = cmd + b'\x00'
            self._canNetwork.send_message(0x1C0 + self.id, cmd)

        self._eh_timer = threading.Timer(180, self._eh_send)
        self._eh_timer.start()

    def _nmt_send(self):
        self._canNetwork.send_message(0x700 + self.id, b'\x05')
        self._canNetwork.send_message(0x700 + self.id, b'\x05\x8A\x01\x00\x9D\x9B\x9D\x91')

        self._nmt_timer = threading.Timer(5, self._nmt_send)
        self._nmt_timer.start()

    def __dl_eh_mpdo_callback(self, can_id, data, timestamp):
        if (data[0] & 0x80) == 0x80 and (data[0] & 0x7F) == self.id:  # DAM
            print("Unsupported DAM DL/EH-MPDO: %s" % binascii.hexlify(data))
        elif data[0] & 0x80 == 0x00: # SAM
            print("Unsupported SAM DL/EH-MPDO: ID: %i %s" % (can_id, binascii.hexlify(data)))  # no use for it

    def __cs_mpdo_callback(self, can_id, data, timestamp):
        if (data[0] & 0x80) == 0x80 and (data[0] & 0x7F) == self.id:  # DAM
            client_id = can_id & 0x3F
            response = bytearray(8)
            response[0] = 0x80 | client_id
            response[1] = 0x80
            response[2] = 0x12
            response[3] = 0x01
            response[4] = 0x40 + client_id
            response[5] = 0x06
            response[6] = 0x00
            if (data[1] == 0x00 and
                data[2] == 0x1F and
                data[3] == 0x00 and
                data[4] == self.id and
                data[5] <= 0x3f and
                data[6] == 0x80 and
                data[7] == 0x12):
                if data[4] == self.id:
                    response[7] = 0x00  # 0x80 if deny
                    server = SdoServer(0x640 + client_id, 0x5C0 + client_id, self._local_node)
                    self._sdo_servers[client_id] = server
                    server.network = self._canNetwork
                    self._canNetwork.subscribe(server.rx_cobid, server.on_request)
                    self._canNetwork.send_message(0x400 + self.id, bytes(response))
                    print("%s node opened for id %i" % (self.name.value, client_id))
            elif (data[1] == 0x01 and
                data[2] == 0x1F and
                data[3] == 0x00 and
                data[5] <= 0x3f and
                data[6] == 0x80 and
                data[7] == 0x12):
                if data[4] == self.id:
                    if client_id in self._sdo_servers:
                        server = self._sdo_servers[client_id]
                        self._canNetwork.unsubscribe(server.rx_cobid, server.on_request)
                        server.network = None
                        self._sdo_servers.pop(client_id)
                    response[7] = 0x80
                    self._canNetwork.send_message(0x400 + self.id, bytes(response))
                    print("%s node closed for id %i" % (self.name.value, client_id))
            elif (data[0] == 0x80 | (self.id & 0x7F) and # DAM to use
                data[1] == 0x80 and # lowbyte  of idx 0x1280
                data[2] == 0x12 and # highbyte of idx 0x1280
                data[3] == 0x01 and # subidx of 0x01
                data[4] == 0x40 + (self.id & 0x7F) and  # lowbyte of 0x640 + client_id
                data[5] == 0x06 and # highbyte of 0x640 + client_id
                data[6] == 0x00 and
                data[7] & 0x7F == 0x00):
                pass
            else:
                print("Unsupported DAM CS-MPDO: %s" % binascii.hexlify(data))
        elif data[0] & 0x80 == 0x00: # SAM
                print("Unsupported SAM CS-MPDO: ID: %i %s" % (can_id, binascii.hexlify(data)))  # no use for it

    def add_analog_output(self, num: int, name: str, unit: Unit, raw_value: bytes):
        if num in self._canAnalogOutputs:
            return
        output = TACANAnalogOutput(self, num, unit, raw_value, True)
        output.name.data = b'\x1f' + (num - 1).to_bytes(1, byteorder='little', signed=False) + name.encode('utf-16le')
        self._canAnalogOutputs[num] = output

        dispatcher.connect(self.__send_analog, "UPDATE", sender=output, weak=False)
        dispatcher.send(num = num, signal = "ADD_CAN-ANALOG-OUTPUT", sender = self)

    def add_digital_output(self, num: int, name: str, value: bool):
        if num in self._canDigitalOutputs:
            return
        output = TACANDigitalOutput(self, num, value.to_bytes(length=2, byteorder='little', signed=False), virtual=True)
        output.name.data = b'\x1f' + (num - 1).to_bytes(1, byteorder='little', signed=False) + name.encode('utf-16le')
        self._canDigitalOutputs[num] = output

        dispatcher.connect(self.__send_digital, "UPDATE", sender=output, weak=False)
        dispatcher.send(num = num, signal = "ADD_CAN-DIGITAL-OUTPUT", sender = self)

    def __send_digital(self):
        if len(self._canDigitalOutputs) == 0:
            return
        cmd = b'\x00\x00\x00\x00'
        values = 0
        for num, v in self._canDigitalOutputs.items():
            values += v.value << (num - 1)
        cmd = values.to_bytes(length=4, byteorder='little', signed=False) + cmd

        self._canNetwork.send_message(0x180 + self.id, cmd)

        # Resetup Timer
        self.__digital_timer.cancel()
        self.__digital_timer = threading.Timer(self.__digital_interval, self.__send_digital)
        self.__digital_timer.start()

    def __send_analog(self):
        for i in range(1, 32, 4):
            self.__send_analog_quadruple(i)

        # Resetup Timer
        self.__analog_timer.cancel()
        self.__analog_timer = threading.Timer(self.__analog_interval, self.__send_analog)
        self.__analog_timer.start()

    def __send_analog_quadruple(self, start: int):
        cob_id = cob_ids[start] + self.id
        cmd = b''
        send = False
        for i in range(start, start + 4):
            if i in self._canAnalogOutputs:
                output = self._canAnalogOutputs[i]  # type: TACANAnalogOutput
                cmd = cmd + output.rawValue
                send = True
            else:
                cmd = cmd + b'\x00\x00'
        assert len(cmd) == 8
        if send:
            self._canNetwork.send_message(cob_id, cmd)

    def open_sdo_to(self, device: GenericDevice) -> SdoClient:
        if self._sdo_node is not None:
            raise ConnectionError("Already open!")
        self._sdo_node = device

        aborted = self.__mpdo_request(device, False)
        if aborted:
            raise ConnectionRefusedError("Refused by node")
        else:
            return self._sdo_client

    def close_sdo(self) -> bool:
        if self._sdo_node is None:
            raise ConnectionError("Not open!")
        closed = self.__mpdo_request(self._sdo_node, True)
        return closed

    def __mpdo_request(self, device: GenericDevice, close: bool):
        resp = threading.Event()
        closed = False

        def answer(can_id, data, timestamp):
            nonlocal closed
            if (data[0] == 0x80 | (self.id & 0x7F) and # DAM to use
                data[1] == 0x80 and # lowbyte  of idx 0x1280
                data[2] == 0x12 and # highbyte of idx 0x1280
                data[3] == 0x01 and # subidx of 0x01
                data[4] == 0x40 + (self.id & 0x7F) and  # lowbyte of 0x640 + client_id
                data[5] == 0x06 and # highbyte of 0x640 + client_id
                data[6] == 0x00 and
                data[7] & 0x7F == 0x00):

                resp.set()
                closed = data[7] == 0x80

        self._canNetwork.subscribe(0x400 + device.id, answer)

                 # DAM  NodeId
        mpdoid = (0x80 + device.id).to_bytes(1, byteorder='little', signed=False)
        server_id = device.id.to_bytes(1, byteorder='little', signed=False)
        client_id = self.id.to_bytes(1, byteorder='little', signed=False)
        if close:
            # Sending MPDO to mpdoid, idx 0x1F00, subidx = 0x01, data = serverId clientId 0x80 0x12
            self._canNetwork.send_message(0x400 + self.id, mpdoid + b'\x01\x1F\x00' + server_id + client_id + b'\x80\x12')
        else:
            # Sending MPDO to mpdoid, idx 0x1F00, subidx = 0x00, data = serverId clientId 0x80 0x12
            self._canNetwork.send_message(0x400 + self.id, mpdoid + b'\x00\x1F\x00' + server_id + client_id + b'\x80\x12')

        finished = resp.wait(10)
        self._canNetwork.unsubscribe(0x400 + device.id, answer)
        if finished:
            if closed:
                self._sdo_node = None
            return closed
        else:
            self._sdo_node = None
            raise TimeoutError("No answer from node")