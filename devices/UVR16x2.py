from devices.TADevice import TADevice

class UVR16x2(TADevice):
    def __init__(self, can_network, can_node):
        super().__init__({
            "maximum_functions": 0x80,
            "type": "UVR16x2",
            "physical_input_max": 16,
            "physical_output_max": 16
        }, can_network, can_node)