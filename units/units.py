from .Unit import Unit
from .DigitalUnit import DigitalUnit
from .RaffstoreUnit import RaffstoreUnit
from .TimeUnit import TimeUnit

units = {
    0: Unit(0, "", "dimensionslos", "", 1, True),
    1: Unit(1, "Grad Celsius", "Temperatur", "°C", 0.1, True),
    2: Unit(2, "Watt/Quadratmeter", "Globalstrahlung", "W/m²", 1, True),
    3: Unit(3, "Liter/Stunde", "Durchfluss", "l/h", 1, True),
    4: Unit(4, "Sekunden", "Zeit", "Sek", 1, True),
    5: Unit(5, "Minuten", "Zeit", "Min", 1, True),
    6: Unit(6, "Liter/Impuls", "Quotient", "l/Imp", 1, True),
    7: Unit(7, "Kelvin", "Temperatur", "K", 1, True),
    8: Unit(8, "%", "rel. Luftfeute", "%", 1, True),
    10: Unit(10, "Kilowatt", "Leistung", "kW", 0.1, True),
    11: Unit(11, "Kilowattstunden", "Wärmemenge", "kWh", 1, True),
    12: Unit(12, "Megawattstunden", "Wärmemenge", "MWh", 1, True),
    13: Unit(13, "Volt", "Spannung", "V", 0.01, True),
    14: Unit(14, "milli Ampere", "Stromstärke", "mA", 0.1, True),
    15: Unit(15, "Stunden", "Zeit", "Std", 1, True),
    16: Unit(16, "Tage", "Zeit", "Tage", 1, True),
    17: Unit(17, "Impulse", "Impulse", "Imp", 1, True),
    18: Unit(18, "Kilo Ohm", "Widerstand", "kOhm", 0.01, True),
    19: Unit(19, "Liter", "Wassermenge", "l", 1, True),
    20: Unit(20, "Kilometer/Stunde", "Windgeschwindigkeit", "km/h", 1, True),
    21: Unit(21, "Hertz", "Frequenz", "Hz", 1, True),
    22: Unit(22, "Liter/Minute", "Durchfluss", "l/min", 1, True),
    23: Unit(23, "bar", "Druck", "bar", 0.01, True),
    25: Unit(25, "Kilometer", "Distanz", "km", 1, True),
    26: Unit(26, "Meter", "Distanz", "m", 1, True),
    27: Unit(27, "Millimeter", "Distanz", "mm", 1, True),
    28: Unit(28, "Kubikmeter", "Luftmenge", "m³", 1, True),
    29: Unit(29, "Hertz/km/Stunde", "Windgeschwindigkeit", "Hz/km/h", 1, True),
    30: Unit(30, "Hertz/Meter/Sek", "Windgeschwindigkeit", "Hz/m/s", 1, True),
    31: Unit(31, "kWh/Impuls", "Leistung", "kWh/Imp", 1, True),
    32: Unit(32, "Kubikmeter/Impuls", "Luftmenge", "m³/Imp", 1, True),
    33: Unit(33, "Millimeter/Impuls", "Niederschlag", "mm/Imp", 1, True),
    34: Unit(34, "Liter/Impuls (4 Komma)", "Durchfluss", "L/Imp", 1, True),
    35: Unit(35, "Liter/Tag", "Durchfluss", "l/d", 1, True),
    36: Unit(36, "Meter/Sekunde", "Geschwindigkeit", "m/s", 1, True),
    37: Unit(37, "Kubikmeter/Minute", "Durchfluss(Gas/Luft)", "m³/min", 1, True),
    38: Unit(38, "Kubikmeter/Stunde", "Durchfluss(Gas/Luft)", "m³/h", 1, True),
    39: Unit(39, "Kubikmeter/Tag", "Durchfluss(Gas/Luft)", "m³/d", 1, True),
    40: Unit(40, "Millimeter/Minute", "Regen", "mm/min", 1, True),
    41: Unit(41, "Millimeter/Stunde", "Regen", "mm/h", 1, True),
    42: Unit(42, "Millimeter/Tag", "Regen", "mm/d", 1, True),

    43: DigitalUnit(43, "Aus/Ein", "", ("Aus", "Ein")),
    44: DigitalUnit(44, "Nein/Ja", "", ("Nein", "Ja")),
    47: DigitalUnit(47, "Stopp/Auf/Zu", "Mischerausgang", ("Stopp", "Auf", "Zu")),

    55: RaffstoreUnit(), # Jalousie Position für Höhe und Neigung bei Lamellen

    59: Unit(59, "Prozent", "Jalousie Position", "%", 1, False), # "Prozent ohne Komma für Jalousie Pos"
    60: TimeUnit() # Uhrzeit (hh:mm)
}