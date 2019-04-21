from devices.TADevice import TADevice

class RSM610(TADevice):
    def __init__(self, can_network, can_node):
        super().__init__({
            "maximum_functions": 44,
            "type": "RSM610",
            "physical_input_max": 6,
            "physical_output_max": 10
        }, can_network, can_node)