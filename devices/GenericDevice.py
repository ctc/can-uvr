import threading

import canopen
from typing import Dict

from taObject import TAString

from taIO import TACANAnalogOutput, TACANDigitalOutput

global_can_lock = threading.Lock()

class GenericDevice:
    _name = None  # type: TAString

    def __init__(self, props, can_network, can_node_id):
        ### props must contain the following attributes: "type"
        self._props = props
        self._canDigitalOutputs = {}  # type Dict[int, TACANDigitalOutput]
        self._canAnalogOutputs = {}  # type Dict[int, TACANAnalogOutput]
        self._canNetwork = can_network  # type: canopen.Network
        self._can_node_id = can_node_id  # type: int
        self._lock = global_can_lock

    @property
    def id(self):
        return self._can_node_id

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._props['type']

    @property
    def canDigitalOutputs(self) -> Dict[int, TACANDigitalOutput]:
        return self._canDigitalOutputs

    @property
    def canAnalogOutputs(self) -> Dict[int, TACANAnalogOutput]:
        return self._canAnalogOutputs

    def getSDO(self, idx, sub_idx):
        return b''

    def setSDO(self, idx, sub_idx, bytes):
        return None