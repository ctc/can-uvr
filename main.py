import canopen
import time

from devices import UVR16x2, RSM610, VirtualDevice
from services import TimeProducer
from services import MQTTClient
from units import units

import logging
logging.basicConfig(level=logging.WARNING)
network = canopen.Network()
network.connect(channel='can0', bustype='socketcan')

devices = []

network.scanner.search(0x3F)

time.sleep(1)
time_start = time.time()
for node_id in network.scanner.nodes:
   if node_id >= 0x40:
       continue
   print("Scanning id " + str(node_id) + "!")
   node = network.add_node(node_id)
   devType = node.sdo.upload(0x23E2, 0x01)
   devType = int.from_bytes(devType, "little")
   if devType == 0x87:
       device = UVR16x2(network, node)
   elif devType == 0x88:
       device = RSM610(network, node)
   else:
       continue # Unsupported

   devices.append(device)
   device.reloadCanOutputs()  # Request CAN outputs over MPDO
   time.sleep(1)

time_end = time.time()
print("Took %f secs for analyzing net" % (time_end - time_start))
time.sleep(2)

time_start = time.time()

for device in devices:
   print("Found %i to be a %s called %s" % (device.id, device.type, device.name.value))
   funcs = device.scanFunctions()
   for num, func in funcs.items():
       print("  %s" % func)
   for oId, output in device.canDigitalOutputs.items():
       print("  %s" % output)
   for oId, output in device.canAnalogOutputs.items():
       print("  %s" % output)
       output.check_link_variable()
   print(" Reads %i Writes %i" % (device.reads, device.writes))
   time.sleep(0.5)

time_end = time.time()
print("Took %f secs for analyzing nodes" % (time_end - time_start))

timer = TimeProducer(network, 120)
timer.start()

from config import config

mqtt_updates = {}

for k, v in config.virtual_devices.items():
    vd = VirtualDevice({
        "type": "VirtualDevice",
        "name": v.name
    }, network, k)
    for out_num, out_obj in v.digital.items():
        vd.add_digital_output(out_num, out_obj.name, out_obj.default_value)
        if "mqtt_listen_uri" in out_obj:
            mqtt_updates[out_obj.mqtt_listen_uri] = vd.canDigitalOutputs[out_num]
    for out_num, out_obj in v.analog.items():
        unit = units[out_obj.unit]
        default_value = out_obj.default_value
        if isinstance(default_value, str):
            default_value = unit.rawifyString(default_value, 2)
        elif isinstance(default_value, (float, int)):
                default_value = unit.rawifyNumber(default_value)
        vd.add_analog_output(out_num, out_obj.name, unit, default_value)
        if "mqtt_listen_uri" in out_obj:
            mqtt_updates[out_obj.mqtt_listen_uri] = vd.canAnalogOutputs[out_num]
    devices.append(vd)

mqtt_client = MQTTClient(network, devices)
mqtt_client.start()

for k, v in mqtt_updates.items():
    mqtt_client.add_listener(k, v)