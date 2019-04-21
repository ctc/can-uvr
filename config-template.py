import utils.dotdict
config = utils.dotdict({
    # Konfiguration für MQTT
    "mqtt": utils.dotdict({
        "host": "127.0.0.1",
        "port": 1883,
        "client_id": "8f594ebdd3ff4373ae69bd7e336ac599", # Irgendein String, der diesen Client von anderen unterscheidet.
        "prefix": "ta_x2/0"
    }),
    "virtual_devices": { # Virtuelle Geräte die CAN-Ausgänge ausgeben können
        2: utils.dotdict({ # 2: Id des Geräts
            "name": "RaspberryPi",
            "digital": { # Digitale CAN-Ausgänge die das Virtuelle Geräte ausgeben soll
                1: utils.dotdict({ # Nummer 1, beginnt bei 1
                    "name": "Linke Garage Tor öffnen", # Name des Ausgangs
                    "default_value": False # Standard-Wert bei Dienststart: False oder True
                }),
                2: utils.dotdict({
                    "name": "Linke Garage Tor schließen",
                    "default_value": False
                }),
                3: utils.dotdict({
                    "name": "Linke Garage Tor lüften",
                    "default_value": False
                }),
                4: utils.dotdict({
                    "name": "Linke Garage Tor deaktivieren",
                    "default_value": False
                }),
                11: utils.dotdict({
                    "name": "Rechte Garage Tor öffnen",
                    "default_value": False
                }),
                12: utils.dotdict({
                    "name": "Rechte Garage Tor schließen",
                    "default_value": False
                }),
                13: utils.dotdict({
                    "name": "Rechte Garage Tor lüften",
                    "default_value": False
                }),
                14: utils.dotdict({
                    "name": "Rechte Garage Tor deaktivieren",
                    "default_value": False
                }),
                21: utils.dotdict({
                    "name": "Terasse Aussensteckdose",
                    "default_value": False
                }),
                22: utils.dotdict({
                    "name": "Lüftungsstrom Soll",
                    "default_value": True
                })
            },
            "analog": {  # Analoge CAN-Ausgänge
                1: utils.dotdict({ # Nummer, s.o. Start bei 1
                    "name": "Ablufttemperatur", # Name des Ausgangs
                    "default_value": "0 °C", # Standard-Wert,
                    "mqtt_listen_uri": "lueftung/zehnder/state/temperature_outlet_before_recuperator",
                    # Zusätzlicher MQTT-Topic auf dem Änderungen publiziert werden können, Inhalt der Nachricht: Wert, optional mit Einheit
                    "unit": 1
                    # Einheit des Ausgangs, Nummer unter units/units.py nachgucken
                }),
                10: utils.dotdict({
                    "name": "Ende Nachtschließung",
                    "default_value": "07:30",
                    "unit": 60
                })
            }
        })
    },
    "device_to_prefix": { # Für fhem-configurator-main.py benötigt
        # Device-Name zu Alias Prefix
        "EG-UVR1": "EG ",
        "EG-RSM1": "EG ",
        "EG-RSM2": "EG ",
        "OG-UVR1": "OG ",
        "OG-RSM1": "OG ",
        "OG-RSM2": "OG ",
        "DG-UVR1": "DG ",
        "DG-RSM1": "DG ",
        "LG-RSM1": "LG ",
        "RG-RSM1": "RG ",
        "RG-RSM2": "RG ",
    },
    "alias_to_room": { # Für fhem-configurator-main.py benötigt. Fügt matchende Objekte automatisch dem Raum hinzu
        # Alias-Prefix + Objektname => Raum
        "EG Büro": "EG Büro",
        "EG Bad 1": "EG Büro",

        "EG Essen": "EG Wohnen",
        "EG Wohnen": "EG Wohnen",
        "EG Terrasse": "EG Wohnen",

        "EG Küche": "EG Küche",

        "LG": "Linke Garage",
        "RG": "Rechte Garage",
    }
})
