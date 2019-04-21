from typing import List
from paho.mqtt import client as mqtt

from pydispatch import dispatcher
import json
import time

import canopen
from canopen.sdo.exceptions import SdoError

from config import config
from functions import JalousieSteuerung

from devices import GenericDevice, TADevice, VirtualDevice
from utils import run_async

class MQTTClient:
    __initialized = False
    def __init__(self, network: canopen.Network, devices: List[GenericDevice]):
        self.__network = network
        self.__devices = devices

        print("Setting up MQTT!")

        self.__client = mqtt.Client(client_id=config.mqtt.client_id)
        self.__client.enable_logger()
        self.__client.on_connect = self.__on_connect
        self.__client.on_message = self.__on_message
        self.__output_listener = {}

    def start(self):
        self.__client.connect(config.mqtt.host, config.mqtt.port, 60)
        self.__client.loop_start()

    def stop(self):
        self.__client.disconnect()
        self.__client.loop_stop()

    def add_listener(self, uri, output):
        self.__output_listener[uri] = output
        @run_async
        def on_change_value(client, userdata, message):
            output.update_from_string(message.payload.decode('cp1252'))

        self.__client.message_callback_add(
            uri,
            on_change_value
        )
        self.__client.subscribe(uri)

    def delete_listener(self, uri):
        del self.__output_listener[uri]
        self.__client.unsubscribe(uri)
        self.__client.message_callback_remove(uri)

    # The callback for when the client receives a CONNACK response from the server.
    def __on_connect(self, client, userdata, flags, rc):
        print("MQTT: Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.

        for device in self.__devices:
            if not isinstance(device, TADevice):
                if isinstance(device, VirtualDevice):
                    dispatcher.connect(self.__add_virtual_analog_output, signal="ADD_CAN-ANALOG-OUTPUT", sender=device, weak=False)
                    dispatcher.connect(self.__add_virtual_digital_output, signal="ADD_CAN-DIGITAL-OUTPUT", sender=device, weak=False)
                    for num in device.canAnalogOutputs.keys():
                        self.__add_virtual_analog_output(device, num)
                    for num in device.canDigitalOutputs.keys():
                        self.__add_virtual_digital_output(device, num)
                continue
            dispatcher.connect(self.__on_device_state, signal="NMT", sender=device, weak = False)
            self.__on_device_state(device)

            dispatcher.connect(self.__add_analog_output, signal="ADD_CAN-ANALOG-OUTPUT", sender=device, weak=False)
            dispatcher.connect(self.__add_digital_output, signal="ADD_CAN-DIGITAL-OUTPUT", sender=device, weak=False)
            for num in device.canAnalogOutputs.keys():
                self.__add_analog_output(device, num)
            for num in device.canDigitalOutputs.keys():
                self.__add_digital_output(device, num)

            dispatcher.connect(self.__add_function, signal="ADD_FUNCTION", sender=device, weak=False)
            for num in device.functions:
                self.__add_function(device, num)

        topic_name = "%s/set/all/top" % config.mqtt.prefix
        if not self.__initialized:
            @run_async
            def on_top(client, userdata, message):
                print("Starting all to top")
                for device in self.__devices:
                    if not isinstance(device, TADevice):
                        continue
                    for func in device.functions.values():
                        if isinstance(func, JalousieSteuerung):
                            try:
                                func.toTop.tap()
                            except SdoError:
                                try:
                                    func.toTop.tap()
                                except SdoError:
                                    print("%s didnt work!" % func.name.str_value)
                            time.sleep(1)
            self.__client.message_callback_add(
                topic_name,
                on_top
            )
        self.__client.subscribe(topic_name)

        topic_name = "%s/set/all/bottom" % config.mqtt.prefix
        if not self.__initialized:
            @run_async
            def on_bottom(client, userdata, message):
                print("Starting all to bottom")
                for device in self.__devices:
                    if not isinstance(device, TADevice):
                        continue
                    for func in device.functions.values():
                        if isinstance(func, JalousieSteuerung):
                            try:
                                func.toBottom.tap()
                            except SdoError:
                                try:
                                    func.toBottom.tap()
                                except SdoError:
                                    print("%s didnt work!" % func.name.str_value)
                            time.sleep(1)

            self.__client.message_callback_add(
                topic_name,
                on_bottom
            )
        self.__client.subscribe(topic_name)
        if self.__initialized:
            for uri, output in self.__output_listener.items():
                self.__client.subscribe(uri)
        self.__initialized = True

    # The callback for when a PUBLISH message is received from the server.
    def __on_message(self, client, userdata, msg):
        print("MQTT: Received message: " + msg.topic+" "+str(msg.payload))

    def __on_device_state(self, sender):
        self.__client.publish("%s/state/%s/nmt" % (config.mqtt.prefix, sender.name.str_value), sender.state,
                              retain=True)

    def __add_digital_output(self, sender: TADevice, num):
        device = sender

        def on_update():
            self.__client.publish(
                "%s/state/%s/can/output/digital/%i/full" % (config.mqtt.prefix, device.name.str_value, num),
                json.dumps({
                    "name": output.name.str_value,
                    "value": output.str_value,
                    "raw": output.value
                }, ensure_ascii=False), retain=True)
            self.__client.publish(
                "%s/state/%s/can/output/digital/%i/value" % (config.mqtt.prefix, device.name.str_value, num),
                output.str_value, retain=True)
            self.__client.publish(
                "%s/state/%s/can/output/digital/%i/int" % (config.mqtt.prefix, device.name.str_value, num),
                output.value, retain=True)

        output = device.canDigitalOutputs[num]
        self.__client.publish(
            "%s/state/%s/can/output/digital/%i/name" % (config.mqtt.prefix, device.name.str_value, num),
            output.name.str_value, retain=True)
        if not self.__initialized:
            dispatcher.connect(on_update, signal="UPDATE", sender=output, weak=False)
        on_update()

    def __add_analog_output(self, sender: TADevice, num):
        device = sender
        
        def on_update():
            self.__client.publish(
                "%s/state/%s/can/output/analog/%i/full" % (config.mqtt.prefix, device.name.str_value, num),
                json.dumps({
                    "name": output.name.str_value,
                    "value": output.str_value,
                    "raw": output.value
                }, ensure_ascii=False), retain=True)
            self.__client.publish(
                "%s/state/%s/can/output/analog/%i/value" % (config.mqtt.prefix, device.name.str_value, num),
                output.str_value, retain=True)
            self.__client.publish(
                "%s/state/%s/can/output/analog/%i/int" % (config.mqtt.prefix, device.name.str_value, num),
                output.value, retain=True)

        output = device.canAnalogOutputs[num]
        self.__client.publish(
            "%s/state/%s/can/output/analog/%i/name" % (config.mqtt.prefix, device.name.str_value, num),
            output.name.str_value, retain=True)
        if not self.__initialized:
            dispatcher.connect(on_update, signal="UPDATE", sender=output, weak=False)
        on_update()

    def __add_virtual_digital_output(self, sender: VirtualDevice, num):
        device = sender

        def on_update():
            self.__client.publish(
                "%s/state/%s/can/output/digital/%i/full" % (config.mqtt.prefix, device.name.str_value, num),
                json.dumps({
                    "name": output.name.str_value,
                    "value": output.str_value,
                    "raw": output.value
                }, ensure_ascii=False), retain=True)
            self.__client.publish(
                "%s/state/%s/can/output/digital/%i/value" % (config.mqtt.prefix, device.name.str_value, num),
                output.str_value, retain=True)

        output = device.canDigitalOutputs[num]
        self.__client.publish(
            "%s/state/%s/can/output/digital/%i/name" % (config.mqtt.prefix, device.name.str_value, num),
            output.name.str_value, retain=True)
        if not self.__initialized:
            dispatcher.connect(on_update, signal="UPDATE", sender=output, weak=False)
        on_update()

        @run_async
        def on_change_value(client, userdata, message):
            output.update_from_string(message.payload.decode('cp1252'))

        topic_name = "%s/set/%s/can/output/digital/%i/set" % (config.mqtt.prefix, device.name.str_value, num)
        self.__client.message_callback_add(
            topic_name,
            on_change_value
        )
        self.__client.subscribe(topic_name)

        @run_async
        def on_tap(client, userdata, message):
            output.update_from_float(1)
            time.sleep(2)
            output.update_from_float(0)

        topic_name = "%s/set/%s/can/output/digital/%i/tap" % (config.mqtt.prefix, device.name.str_value, num)
        self.__client.message_callback_add(
            topic_name,
            on_tap
        )
        self.__client.subscribe(topic_name)

    def __add_virtual_analog_output(self, sender: VirtualDevice, num):
        device = sender

        def on_update():
            self.__client.publish(
                "%s/state/%s/can/output/analog/%i/full" % (config.mqtt.prefix, device.name.str_value, num),
                json.dumps({
                    "name": output.name.str_value,
                    "value": output.str_value,
                    "raw": output.value
                }, ensure_ascii=False), retain=True)
            self.__client.publish(
                "%s/state/%s/can/output/analog/%i/value" % (config.mqtt.prefix, device.name.str_value, num),
                output.str_value, retain=True)

        output = device.canAnalogOutputs[num]
        self.__client.publish(
            "%s/state/%s/can/output/analog/%i/name" % (config.mqtt.prefix, device.name.str_value, num),
            output.name.str_value, retain=True)
        if not self.__initialized:
            dispatcher.connect(on_update, signal="UPDATE", sender=output, weak=False)

        on_update()

        @run_async
        def on_change_value(client, userdata, message):
            output.update_from_string(message.payload.decode("cp1252"))

        topic_name = "%s/set/%s/can/output/analog/%i/set" % (config.mqtt.prefix, device.name.str_value, num)
        self.__client.message_callback_add(
            topic_name,
            on_change_value
        )
        self.__client.subscribe(topic_name)

    def __add_function(self, sender: TADevice, num):
        device = sender
        function = device.functions[num]

        self.__client.publish(
            "%s/state/%s/functions/%i/typId" % (config.mqtt.prefix, device.name.str_value, num),
            str(function.typ.stringSubIdx), retain=True)
        self.__client.publish(
            "%s/state/%s/functions/%i/typName" % (config.mqtt.prefix, device.name.str_value, num),
            function.typ.str_value, retain=True)

        if isinstance(function, JalousieSteuerung):
            pos = function.position
            istPos = pos.istPosition

            if not self.__initialized:
                def on_update_ist_pos():
                    self.__client.publish(
                        "%s/state/%s/functions/%i/current/height" % (config.mqtt.prefix, device.name.str_value, num),
                        istPos.jalousieProzent(), retain=True)
                    self.__client.publish(
                        "%s/state/%s/functions/%i/current/tilt" % (config.mqtt.prefix, device.name.str_value, num),
                        istPos.lamelleProzent(), retain=True)

                dispatcher.connect(on_update_ist_pos, signal="UPDATE", sender=istPos, weak=False)
                on_update_ist_pos()
                istPos.setup_periodic(30)

                def on_update_auto():
                    self.__client.publish(
                        "%s/state/%s/functions/%i/current/automatic" % (config.mqtt.prefix, device.name.str_value, num),
                        function.autobetrieb.value, retain=True)

                dispatcher.connect(on_update_auto, signal="UPDATE", sender=function.autobetrieb, weak=False)
                on_update_auto()
                function.autobetrieb.setup_periodic(30)

            @run_async
            def on_change_position(client, userdata, message):
                try:
                    split = message.payload.split(b':')
                    height = int(split[0])
                    tilt = int(split[1])
                    try:
                        pos.set(height, tilt)
                    except SdoError:
                        try:
                            pos.set(height, tilt)
                        except SdoError:
                            print("This one didnt work! %s %s: %s" % (device.name.str_value, num, message))
                    pos.sollPosition.reload()
                except ValueError:
                    print("Wrong value %s" %message)

            topic_name = "%s/set/%s/functions/%i/position" % (config.mqtt.prefix, device.name.str_value, num)
            self.__client.message_callback_add(
                topic_name,
                on_change_position
            )
            self.__client.subscribe(topic_name)

            @run_async
            def on_trigger_auto(client, userdata, message):
                try:
                    function.triggerAuto.tap()
                except SdoError:
                    try:
                        function.triggerAuto.tap()
                    except SdoError:
                        print("Automaticing didnt work! %s %s" % (device.name.str_value, num))

            topic_name = "%s/set/%s/functions/%i/auto/tap" % (config.mqtt.prefix, device.name.str_value, num)
            self.__client.message_callback_add(
                topic_name,
                on_trigger_auto
            )
            self.__client.subscribe(topic_name)

            @run_async
            def on_trigger_horizontal(client, userdata, message):
                try:
                    function.toHorizontal.tap()
                except SdoError:
                    try:
                        function.toHorizontal.tap()
                    except SdoError:
                        print("Horizontaling didnt work! %s %s" % (device.name.str_value, num))

            topic_name = "%s/set/%s/functions/%i/horizontal/tap" % (config.mqtt.prefix, device.name.str_value, num)
            self.__client.message_callback_add(
                topic_name,
                on_trigger_horizontal
            )
            self.__client.subscribe(topic_name)