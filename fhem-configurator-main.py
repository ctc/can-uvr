#!/usr/bin/python3.4

# Requires the ta.template file to be present in the /FHEM/lib/AttrTemplate folder

import argparse

parser = argparse.ArgumentParser(description='Adding defined functions/outputs to fhem')
parser.add_argument("-a", "--ip", dest='fhem_ip', type=str, default='127.0.0.1', help='IP of the fhem instance (def: 127.0.0.1)')
parser.add_argument("-p", "--port", dest='fhem_port', type=int, default=7072, help='(Telnet) Port of the fhem instance (def: 7072)')
parser.add_argument("-u", "--username", dest='fhem_username', type=str, default='', help='Username to use')
parser.add_argument("-k", "--password", dest='fhem_password', type=str, default='', help='Password to use')

parser.add_argument('-A', "--analog", dest='add_analog', default=False, help='If analogue can outputs shall be added (def: false)', action='store_true')
parser.add_argument('-D', "--digital", dest='add_digital', default=False, help='If jalousie can outputs shall be added (def: false)', action='store_true')
parser.add_argument('-J', "--jalousie", dest='add_jalousie', default=False, help='If jalousie functions shall be added (def: false)', action='store_true')

parser.add_argument("node_id", type=int, nargs='*', help='Only search on these nodes (def: all)')

args = parser.parse_args()

import canopen
import time
import fhem
import sys

from devices import UVR16x2, RSM610, VirtualDevice
from functions import JalousieSteuerung
from config import config

network = canopen.Network()
network.connect(channel='can0', bustype='socketcan')

network.scanner.search(0x3F)

time.sleep(1)

fh = fhem.Fhem(args.fhem_ip, port=args.fhem_port, protocol='telnet', username=args.fhem_username, password=args.fhem_password)
fh.connect()
if fh.connected():
    print("Connected to FHEM!")
else:
    print("Couldnt connect to FHEM!")
    exit(0)

vd = VirtualDevice({
    "type": "VirtualDevice",
    "name": "FHEM Configurator Script"
}, network, 63)

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes": 
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def idify(string):
    return string.lower().replace("-", "_").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace(" / ", "_").replace(" ", "_").replace("ß", "ss")

time_start = time.time()

for node_id in network.scanner.nodes:
    if node_id >= 0x40:
        continue
    if len(args.node_id) > 0 and node_id not in args.node_id:
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
    device.reloadCanOutputs()
    time.sleep(2)

    print("Found %i to be a %s called %s" % (device.id, device.type, device.name.value))
    device.use_virtual_device(vd)
    funcs = device.scanFunctions()
    for num, func in funcs.items():
        print("  Function #%i %s" % (num, func.name.value))
        if isinstance(func, JalousieSteuerung) and args.add_jalousie:
            func_name = func.name.value
            name = "%s_%s" % (idify(device.name.value), idify(func_name))

            cmd = "define %s MQTT2_DEVICE" % name
            fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)
            cmd = "set %s attrTemplate Z_01_ta_function_blinds_de %s %s %i" % (name, config.mqtt.prefix, device.name.value, func.num)
            fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)

            alias = "%s%s" % (config.device_to_prefix[device.name.value], func_name)
            cmd = "attr %s alias %s" % (name, alias)
            fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)

            for k, v in config.alias_to_room.items():
                if k in alias:
                    cmd = "attr %s room %s" % (name, v)
                    fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)
                    break

            cmd = "attr %s group Jalousie" % name
            fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)
            time.sleep(0.1)

    for num, output in device.canAnalogOutputs.items():
        print("  Analog Output #%i %s" % (num, output.name.value))
        if not args.add_analog:
            continue
        if not query_yes_no("   Add to fhem?", "no"):
            continue
        output_name = output.name.value
        name = "%s_%s" % (idify(device.name.value), idify(output_name))
        cmd = "define %s MQTT2_DEVICE" % name
        fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)
        cmd = "set %s attrTemplate Z_01_ta_can_output_analog_de %s %s %i" % (name, config.mqtt.prefix, device.name.value, num)
        fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)

        alias = "%s%s" % (config.device_to_prefix[device.name.value], output_name)
        cmd = "attr %s alias %s" % (name, alias)
        fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)

        for k, v in config.alias_to_room.items():
            if k in alias:
                cmd = "attr %s room %s" % (name, v)
                fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)
                break

    for num, output in device.canDigitalOutputs.items():
        print("  Digital Output #%i %s" % (num, output.name.value))
        if not args.add_digital:
            continue
        if not query_yes_no("   Add to fhem?", "no"):
            continue
        output_name = output.name.value
        name = "%s_%s" % (idify(device.name.value), idify(output_name))
        cmd = "define %s MQTT2_DEVICE" % name
        fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)
        cmd = "set %s attrTemplate Z_01_ta_can_output_digital_de %s %s %i" % (name, config.mqtt.prefix, device.name.value, num)
        fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)

        alias = "%s%s" % (config.device_to_prefix[device.name.value], output_name)
        cmd = "attr %s alias %s" % (name, alias)
        fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)

        for k, v in config.alias_to_room.items():
            if k in alias:
                cmd = "attr %s room %s" % (name, v)
                fh.send_cmd(cmd); print("   Send cmd: %s" % cmd)
                break

    device.unuse_virtual_device()
    print(" Reads %i Writes %i" % (device.reads, device.writes))
    time.sleep(1)

time_end = time.time()
print("Took %f secs for analyzing nodes" % (time_end - time_start))

vd.stop()
network.disconnect()
exit(0)