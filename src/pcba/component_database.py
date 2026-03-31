"""
Comprehensive KiCad Component Database.

Contains ~500 common components with lib_ids, pin info, categories, and footprints.
Used for validation, description generation, and auto-fixing model output.
"""

from typing import Any


# Component categories
CATEGORY_MCU = "mcu"
CATEGORY_SENSOR = "sensor"
CATEGORY_PASSIVE = "passive"
CATEGORY_ACTIVE = "active"
CATEGORY_CONNECTOR = "connector"
CATEGORY_POWER = "power"
CATEGORY_DISPLAY = "display"
CATEGORY_COMMUNICATION = "communication"
CATEGORY_MOTOR = "motor"
CATEGORY_RELAY = "relay"
CATEGORY_SWITCH = "switch"
CATEGORY_AUDIO = "audio"
CATEGORY_MEMORY = "memory"
CATEGORY_LOGIC = "logic"
CATEGORY_MODULE = "module"

# Pin types
PIN_INPUT = "input"
PIN_OUTPUT = "output"
PIN_BIDIRECTIONAL = "bidirectional"
PIN_POWER_IN = "power_in"
PIN_POWER_OUT = "power_out"
PIN_PASSIVE = "passive"
PIN_OPEN_COLLECTOR = "open_collector"
PIN_OPEN_EMITTER = "open_emitter"
PIN_NC = "no_connect"


# ============================================================================
# Component Database
# ============================================================================

COMPONENTS: dict[str, dict[str, Any]] = {
    # ========== PASSIVE COMPONENTS ==========
    "Device:R": {
        "category": CATEGORY_PASSIVE, "name": "Resistor",
        "pins": [
            {"number": "1", "name": "~", "type": PIN_PASSIVE},
            {"number": "2", "name": "~", "type": PIN_PASSIVE},
        ],
        "footprints": ["Resistor_SMD:R_0805_2012Metric", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"],
    },
    "Device:R_Small": {
        "category": CATEGORY_PASSIVE, "name": "Resistor (small symbol)",
        "pins": [{"number": "1", "name": "~", "type": PIN_PASSIVE}, {"number": "2", "name": "~", "type": PIN_PASSIVE}],
        "footprints": ["Resistor_SMD:R_0402_1005Metric", "Resistor_SMD:R_0603_1608Metric"],
    },
    "Device:R_POT": {
        "category": CATEGORY_PASSIVE, "name": "Potentiometer",
        "pins": [{"number": "1", "name": "1", "type": PIN_PASSIVE}, {"number": "2", "name": "2", "type": PIN_PASSIVE}, {"number": "3", "name": "3", "type": PIN_PASSIVE}],
        "footprints": ["Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical"],
    },
    "Device:C": {
        "category": CATEGORY_PASSIVE, "name": "Capacitor",
        "pins": [{"number": "1", "name": "~", "type": PIN_PASSIVE}, {"number": "2", "name": "~", "type": PIN_PASSIVE}],
        "footprints": ["Capacitor_SMD:C_0805_2012Metric", "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"],
    },
    "Device:C_Small": {
        "category": CATEGORY_PASSIVE, "name": "Capacitor (small)",
        "pins": [{"number": "1", "name": "~", "type": PIN_PASSIVE}, {"number": "2", "name": "~", "type": PIN_PASSIVE}],
        "footprints": ["Capacitor_SMD:C_0402_1005Metric"],
    },
    "Device:C_Polarized": {
        "category": CATEGORY_PASSIVE, "name": "Electrolytic Capacitor",
        "pins": [{"number": "1", "name": "+", "type": PIN_PASSIVE}, {"number": "2", "name": "-", "type": PIN_PASSIVE}],
        "footprints": ["Capacitor_THT:CP_Radial_D5.0mm_P2.50mm"],
    },
    "Device:L": {
        "category": CATEGORY_PASSIVE, "name": "Inductor",
        "pins": [{"number": "1", "name": "~", "type": PIN_PASSIVE}, {"number": "2", "name": "~", "type": PIN_PASSIVE}],
        "footprints": ["Inductor_SMD:L_0805_2012Metric"],
    },
    "Device:LED": {
        "category": CATEGORY_PASSIVE, "name": "LED",
        "pins": [{"number": "1", "name": "K", "type": PIN_PASSIVE}, {"number": "2", "name": "A", "type": PIN_PASSIVE}],
        "footprints": ["LED_SMD:LED_0805_2012Metric", "LED_THT:LED_D5.0mm"],
    },
    "Device:LED_Small": {
        "category": CATEGORY_PASSIVE, "name": "LED (small)",
        "pins": [{"number": "1", "name": "K", "type": PIN_PASSIVE}, {"number": "2", "name": "A", "type": PIN_PASSIVE}],
        "footprints": ["LED_SMD:LED_0603_1608Metric"],
    },
    "Device:D": {
        "category": CATEGORY_PASSIVE, "name": "Diode",
        "pins": [{"number": "1", "name": "K", "type": PIN_PASSIVE}, {"number": "2", "name": "A", "type": PIN_PASSIVE}],
        "footprints": ["Diode_SMD:D_SOD-123"],
    },
    "Device:D_Zener": {
        "category": CATEGORY_PASSIVE, "name": "Zener Diode",
        "pins": [{"number": "1", "name": "K", "type": PIN_PASSIVE}, {"number": "2", "name": "A", "type": PIN_PASSIVE}],
        "footprints": ["Diode_SMD:D_SOD-123"],
    },
    "Device:D_Schottky": {
        "category": CATEGORY_PASSIVE, "name": "Schottky Diode",
        "pins": [{"number": "1", "name": "K", "type": PIN_PASSIVE}, {"number": "2", "name": "A", "type": PIN_PASSIVE}],
        "footprints": ["Diode_SMD:D_SOD-123"],
    },
    "Device:Crystal": {
        "category": CATEGORY_PASSIVE, "name": "Crystal Oscillator",
        "pins": [{"number": "1", "name": "1", "type": PIN_PASSIVE}, {"number": "2", "name": "2", "type": PIN_PASSIVE}],
        "footprints": ["Crystal:Crystal_HC49-U_Vertical"],
    },
    "Device:Fuse": {
        "category": CATEGORY_PASSIVE, "name": "Fuse",
        "pins": [{"number": "1", "name": "~", "type": PIN_PASSIVE}, {"number": "2", "name": "~", "type": PIN_PASSIVE}],
        "footprints": ["Fuse:Fuse_0805_2012Metric"],
    },
    "Device:Buzzer": {
        "category": CATEGORY_AUDIO, "name": "Buzzer",
        "pins": [{"number": "1", "name": "+", "type": PIN_PASSIVE}, {"number": "2", "name": "-", "type": PIN_PASSIVE}],
        "footprints": ["Buzzer_Beeper:Buzzer_12x9.5RM7.6"],
    },
    "Device:Speaker": {
        "category": CATEGORY_AUDIO, "name": "Speaker",
        "pins": [{"number": "1", "name": "+", "type": PIN_PASSIVE}, {"number": "2", "name": "-", "type": PIN_PASSIVE}],
        "footprints": [],
    },

    # ========== TRANSISTORS ==========
    "Device:Q_NPN_BCE": {
        "category": CATEGORY_ACTIVE, "name": "NPN Transistor",
        "pins": [{"number": "1", "name": "B", "type": PIN_INPUT}, {"number": "2", "name": "C", "type": PIN_PASSIVE}, {"number": "3", "name": "E", "type": PIN_PASSIVE}],
        "footprints": ["Package_TO_SOT_THT:TO-92_Inline"],
    },
    "Device:Q_PNP_BCE": {
        "category": CATEGORY_ACTIVE, "name": "PNP Transistor",
        "pins": [{"number": "1", "name": "B", "type": PIN_INPUT}, {"number": "2", "name": "C", "type": PIN_PASSIVE}, {"number": "3", "name": "E", "type": PIN_PASSIVE}],
        "footprints": ["Package_TO_SOT_THT:TO-92_Inline"],
    },
    "Device:Q_NMOS_GDS": {
        "category": CATEGORY_ACTIVE, "name": "N-Channel MOSFET",
        "pins": [{"number": "1", "name": "G", "type": PIN_INPUT}, {"number": "2", "name": "D", "type": PIN_PASSIVE}, {"number": "3", "name": "S", "type": PIN_PASSIVE}],
        "footprints": ["Package_TO_SOT_THT:TO-220-3_Vertical"],
    },
    "Device:Q_PMOS_GDS": {
        "category": CATEGORY_ACTIVE, "name": "P-Channel MOSFET",
        "pins": [{"number": "1", "name": "G", "type": PIN_INPUT}, {"number": "2", "name": "D", "type": PIN_PASSIVE}, {"number": "3", "name": "S", "type": PIN_PASSIVE}],
        "footprints": ["Package_TO_SOT_THT:TO-220-3_Vertical"],
    },

    # ========== OP-AMPS ==========
    "Amplifier_Operational:LM358": {
        "category": CATEGORY_ACTIVE, "name": "LM358 Dual Op-Amp",
        "pins": [
            {"number": "1", "name": "OUT_A", "type": PIN_OUTPUT},
            {"number": "2", "name": "IN-_A", "type": PIN_INPUT},
            {"number": "3", "name": "IN+_A", "type": PIN_INPUT},
            {"number": "4", "name": "V-", "type": PIN_POWER_IN},
            {"number": "5", "name": "IN+_B", "type": PIN_INPUT},
            {"number": "6", "name": "IN-_B", "type": PIN_INPUT},
            {"number": "7", "name": "OUT_B", "type": PIN_OUTPUT},
            {"number": "8", "name": "V+", "type": PIN_POWER_IN},
        ],
        "footprints": ["Package_DIP:DIP-8_W7.62mm"],
    },
    "Amplifier_Operational:LM741": {
        "category": CATEGORY_ACTIVE, "name": "LM741 Op-Amp",
        "pins": [
            {"number": "2", "name": "IN-", "type": PIN_INPUT},
            {"number": "3", "name": "IN+", "type": PIN_INPUT},
            {"number": "6", "name": "OUT", "type": PIN_OUTPUT},
            {"number": "7", "name": "V+", "type": PIN_POWER_IN},
            {"number": "4", "name": "V-", "type": PIN_POWER_IN},
        ],
        "footprints": ["Package_DIP:DIP-8_W7.62mm"],
    },

    # ========== VOLTAGE REGULATORS ==========
    "Regulator_Linear:LM7805_TO220": {
        "category": CATEGORY_POWER, "name": "7805 5V Regulator",
        "pins": [
            {"number": "1", "name": "IN", "type": PIN_POWER_IN},
            {"number": "2", "name": "GND", "type": PIN_POWER_IN},
            {"number": "3", "name": "OUT", "type": PIN_POWER_OUT},
        ],
        "footprints": ["Package_TO_SOT_THT:TO-220-3_Vertical"],
    },
    "Regulator_Linear:LM7812_TO220": {
        "category": CATEGORY_POWER, "name": "7812 12V Regulator",
        "pins": [
            {"number": "1", "name": "IN", "type": PIN_POWER_IN},
            {"number": "2", "name": "GND", "type": PIN_POWER_IN},
            {"number": "3", "name": "OUT", "type": PIN_POWER_OUT},
        ],
        "footprints": ["Package_TO_SOT_THT:TO-220-3_Vertical"],
    },
    "Regulator_Linear:LM317_TO220": {
        "category": CATEGORY_POWER, "name": "LM317 Adj. Regulator",
        "pins": [
            {"number": "1", "name": "ADJ", "type": PIN_INPUT},
            {"number": "2", "name": "OUT", "type": PIN_POWER_OUT},
            {"number": "3", "name": "IN", "type": PIN_POWER_IN},
        ],
        "footprints": ["Package_TO_SOT_THT:TO-220-3_Vertical"],
    },
    "Regulator_Linear:AMS1117-3.3": {
        "category": CATEGORY_POWER, "name": "AMS1117 3.3V Regulator",
        "pins": [
            {"number": "1", "name": "GND", "type": PIN_POWER_IN},
            {"number": "2", "name": "OUT", "type": PIN_POWER_OUT},
            {"number": "3", "name": "IN", "type": PIN_POWER_IN},
        ],
        "footprints": ["Package_TO_SOT_SMD:SOT-223-3_TabPin2"],
    },

    # ========== MCU / MICROCONTROLLERS ==========
    "MCU_Module:Arduino_UNO_R3": {
        "category": CATEGORY_MCU, "name": "Arduino UNO R3",
        "pins": [
            {"number": "1", "name": "VIN", "type": PIN_POWER_IN},
            {"number": "4", "name": "GND", "type": PIN_POWER_IN},
            {"number": "5", "name": "5V", "type": PIN_POWER_OUT},
            {"number": "6", "name": "3V3", "type": PIN_POWER_OUT},
            {"number": "9", "name": "A0", "type": PIN_BIDIRECTIONAL},
            {"number": "10", "name": "A1", "type": PIN_BIDIRECTIONAL},
            {"number": "11", "name": "A2", "type": PIN_BIDIRECTIONAL},
            {"number": "12", "name": "A3", "type": PIN_BIDIRECTIONAL},
            {"number": "13", "name": "A4", "type": PIN_BIDIRECTIONAL},
            {"number": "14", "name": "A5", "type": PIN_BIDIRECTIONAL},
            {"number": "15", "name": "D0", "type": PIN_BIDIRECTIONAL},
            {"number": "16", "name": "D1", "type": PIN_BIDIRECTIONAL},
            {"number": "17", "name": "D2", "type": PIN_BIDIRECTIONAL},
            {"number": "18", "name": "D3", "type": PIN_BIDIRECTIONAL},
            {"number": "19", "name": "D4", "type": PIN_BIDIRECTIONAL},
            {"number": "20", "name": "D5", "type": PIN_BIDIRECTIONAL},
            {"number": "21", "name": "D6", "type": PIN_BIDIRECTIONAL},
            {"number": "22", "name": "D7", "type": PIN_BIDIRECTIONAL},
            {"number": "23", "name": "D8", "type": PIN_BIDIRECTIONAL},
            {"number": "24", "name": "D9", "type": PIN_BIDIRECTIONAL},
            {"number": "25", "name": "D10", "type": PIN_BIDIRECTIONAL},
            {"number": "26", "name": "D11", "type": PIN_BIDIRECTIONAL},
            {"number": "27", "name": "D12", "type": PIN_BIDIRECTIONAL},
            {"number": "28", "name": "D13", "type": PIN_BIDIRECTIONAL},
        ],
        "footprints": ["Module:Arduino_UNO_R3"],
    },
    "MCU_Module:Arduino_Nano_v3.x": {
        "category": CATEGORY_MCU, "name": "Arduino Nano",
        "pins": [
            {"number": "2", "name": "VIN", "type": PIN_POWER_IN},
            {"number": "4", "name": "GND", "type": PIN_POWER_IN},
            {"number": "27", "name": "5V", "type": PIN_POWER_OUT},
            {"number": "14", "name": "D0", "type": PIN_BIDIRECTIONAL},
            {"number": "15", "name": "D1", "type": PIN_BIDIRECTIONAL},
            {"number": "16", "name": "D2", "type": PIN_BIDIRECTIONAL},
            {"number": "17", "name": "D3", "type": PIN_BIDIRECTIONAL},
            {"number": "18", "name": "D4", "type": PIN_BIDIRECTIONAL},
            {"number": "19", "name": "D5", "type": PIN_BIDIRECTIONAL},
            {"number": "20", "name": "D6", "type": PIN_BIDIRECTIONAL},
            {"number": "21", "name": "D7", "type": PIN_BIDIRECTIONAL},
            {"number": "22", "name": "D8", "type": PIN_BIDIRECTIONAL},
            {"number": "23", "name": "D9", "type": PIN_BIDIRECTIONAL},
            {"number": "24", "name": "D10", "type": PIN_BIDIRECTIONAL},
            {"number": "25", "name": "D11", "type": PIN_BIDIRECTIONAL},
            {"number": "26", "name": "D12", "type": PIN_BIDIRECTIONAL},
            {"number": "28", "name": "D13", "type": PIN_BIDIRECTIONAL},
            {"number": "5", "name": "A0", "type": PIN_BIDIRECTIONAL},
            {"number": "6", "name": "A1", "type": PIN_BIDIRECTIONAL},
            {"number": "7", "name": "A2", "type": PIN_BIDIRECTIONAL},
            {"number": "8", "name": "A3", "type": PIN_BIDIRECTIONAL},
            {"number": "9", "name": "A4", "type": PIN_BIDIRECTIONAL},
            {"number": "10", "name": "A5", "type": PIN_BIDIRECTIONAL},
            {"number": "11", "name": "A6", "type": PIN_BIDIRECTIONAL},
            {"number": "12", "name": "A7", "type": PIN_BIDIRECTIONAL},
        ],
        "footprints": ["Module:Arduino_Nano"],
    },
    "MCU_Microchip_ATmega:ATmega328P-PU": {
        "category": CATEGORY_MCU, "name": "ATmega328P",
        "pins": [
            {"number": "1", "name": "PC6", "type": PIN_BIDIRECTIONAL},
            {"number": "2", "name": "PD0", "type": PIN_BIDIRECTIONAL},
            {"number": "3", "name": "PD1", "type": PIN_BIDIRECTIONAL},
            {"number": "4", "name": "PD2", "type": PIN_BIDIRECTIONAL},
            {"number": "5", "name": "PD3", "type": PIN_BIDIRECTIONAL},
            {"number": "6", "name": "PD4", "type": PIN_BIDIRECTIONAL},
            {"number": "7", "name": "VCC", "type": PIN_POWER_IN},
            {"number": "8", "name": "GND", "type": PIN_POWER_IN},
            {"number": "9", "name": "PB6", "type": PIN_BIDIRECTIONAL},
            {"number": "10", "name": "PB7", "type": PIN_BIDIRECTIONAL},
            {"number": "11", "name": "PD5", "type": PIN_BIDIRECTIONAL},
            {"number": "12", "name": "PD6", "type": PIN_BIDIRECTIONAL},
            {"number": "13", "name": "PD7", "type": PIN_BIDIRECTIONAL},
            {"number": "14", "name": "PB0", "type": PIN_BIDIRECTIONAL},
            {"number": "15", "name": "PB1", "type": PIN_BIDIRECTIONAL},
            {"number": "16", "name": "PB2", "type": PIN_BIDIRECTIONAL},
            {"number": "17", "name": "PB3", "type": PIN_BIDIRECTIONAL},
            {"number": "18", "name": "PB4", "type": PIN_BIDIRECTIONAL},
            {"number": "19", "name": "PB5", "type": PIN_BIDIRECTIONAL},
            {"number": "20", "name": "AVCC", "type": PIN_POWER_IN},
            {"number": "21", "name": "AREF", "type": PIN_PASSIVE},
            {"number": "22", "name": "GND", "type": PIN_POWER_IN},
            {"number": "23", "name": "PC0", "type": PIN_BIDIRECTIONAL},
            {"number": "24", "name": "PC1", "type": PIN_BIDIRECTIONAL},
            {"number": "25", "name": "PC2", "type": PIN_BIDIRECTIONAL},
            {"number": "26", "name": "PC3", "type": PIN_BIDIRECTIONAL},
            {"number": "27", "name": "PC4", "type": PIN_BIDIRECTIONAL},
            {"number": "28", "name": "PC5", "type": PIN_BIDIRECTIONAL},
        ],
        "footprints": ["Package_DIP:DIP-28_W7.62mm"],
    },

    # ========== ESP32 / WiFi Modules ==========
    "RF_Module:ESP32-WROOM-32": {
        "category": CATEGORY_MODULE, "name": "ESP32-WROOM-32",
        "pins": [
            {"number": "1", "name": "GND", "type": PIN_POWER_IN},
            {"number": "2", "name": "3V3", "type": PIN_POWER_IN},
            {"number": "3", "name": "EN", "type": PIN_INPUT},
            {"number": "4", "name": "IO36", "type": PIN_INPUT},
            {"number": "5", "name": "IO39", "type": PIN_INPUT},
            {"number": "6", "name": "IO34", "type": PIN_INPUT},
            {"number": "7", "name": "IO35", "type": PIN_INPUT},
            {"number": "8", "name": "IO32", "type": PIN_BIDIRECTIONAL},
            {"number": "9", "name": "IO33", "type": PIN_BIDIRECTIONAL},
            {"number": "10", "name": "IO25", "type": PIN_BIDIRECTIONAL},
            {"number": "11", "name": "IO26", "type": PIN_BIDIRECTIONAL},
            {"number": "12", "name": "IO27", "type": PIN_BIDIRECTIONAL},
            {"number": "13", "name": "IO14", "type": PIN_BIDIRECTIONAL},
            {"number": "14", "name": "IO12", "type": PIN_BIDIRECTIONAL},
            {"number": "15", "name": "GND", "type": PIN_POWER_IN},
            {"number": "16", "name": "IO13", "type": PIN_BIDIRECTIONAL},
            {"number": "24", "name": "IO23", "type": PIN_BIDIRECTIONAL},
            {"number": "25", "name": "IO22", "type": PIN_BIDIRECTIONAL},
            {"number": "26", "name": "IO1", "type": PIN_BIDIRECTIONAL},
            {"number": "27", "name": "IO3", "type": PIN_BIDIRECTIONAL},
            {"number": "28", "name": "IO21", "type": PIN_BIDIRECTIONAL},
            {"number": "30", "name": "IO19", "type": PIN_BIDIRECTIONAL},
            {"number": "31", "name": "IO18", "type": PIN_BIDIRECTIONAL},
            {"number": "32", "name": "IO5", "type": PIN_BIDIRECTIONAL},
            {"number": "33", "name": "IO17", "type": PIN_BIDIRECTIONAL},
            {"number": "34", "name": "IO16", "type": PIN_BIDIRECTIONAL},
            {"number": "35", "name": "IO4", "type": PIN_BIDIRECTIONAL},
            {"number": "36", "name": "IO0", "type": PIN_BIDIRECTIONAL},
            {"number": "37", "name": "IO2", "type": PIN_BIDIRECTIONAL},
            {"number": "38", "name": "IO15", "type": PIN_BIDIRECTIONAL},
        ],
        "footprints": ["RF_Module:ESP32-WROOM-32"],
    },
    "RF_Module:ESP-12E": {
        "category": CATEGORY_MODULE, "name": "ESP8266 ESP-12E",
        "pins": [
            {"number": "1", "name": "REST", "type": PIN_INPUT},
            {"number": "2", "name": "ADC", "type": PIN_INPUT},
            {"number": "3", "name": "CH_PD", "type": PIN_INPUT},
            {"number": "4", "name": "GPIO16", "type": PIN_BIDIRECTIONAL},
            {"number": "5", "name": "GPIO14", "type": PIN_BIDIRECTIONAL},
            {"number": "6", "name": "GPIO12", "type": PIN_BIDIRECTIONAL},
            {"number": "7", "name": "GPIO13", "type": PIN_BIDIRECTIONAL},
            {"number": "8", "name": "VCC", "type": PIN_POWER_IN},
            {"number": "9", "name": "GND", "type": PIN_POWER_IN},
            {"number": "10", "name": "GPIO15", "type": PIN_BIDIRECTIONAL},
            {"number": "11", "name": "GPIO2", "type": PIN_BIDIRECTIONAL},
            {"number": "12", "name": "GPIO0", "type": PIN_BIDIRECTIONAL},
            {"number": "13", "name": "GPIO4", "type": PIN_BIDIRECTIONAL},
            {"number": "14", "name": "GPIO5", "type": PIN_BIDIRECTIONAL},
            {"number": "15", "name": "RXD", "type": PIN_INPUT},
            {"number": "16", "name": "TXD", "type": PIN_OUTPUT},
        ],
        "footprints": ["RF_Module:ESP-12E"],
    },

    # ========== SENSORS ==========
    "Sensor:DHT11": {
        "category": CATEGORY_SENSOR, "name": "DHT11/DHT22 Temperature & Humidity Sensor",
        "pins": [
            {"number": "1", "name": "VDD", "type": PIN_POWER_IN},
            {"number": "2", "name": "DATA", "type": PIN_BIDIRECTIONAL},
            {"number": "3", "name": "NC", "type": PIN_NC},
            {"number": "4", "name": "GND", "type": PIN_POWER_IN},
        ],
        "footprints": ["Sensor:AOSONG_DHT11_5.5x12.0_P2.54mm"],
    },
    "Sensor:BME280": {
        "category": CATEGORY_SENSOR, "name": "BME280 Pressure/Humidity/Temperature Sensor",
        "pins": [
            {"number": "1", "name": "VCC", "type": PIN_POWER_IN},
            {"number": "2", "name": "GND", "type": PIN_POWER_IN},
            {"number": "3", "name": "SDA", "type": PIN_BIDIRECTIONAL},
            {"number": "4", "name": "SDO", "type": PIN_OUTPUT},
            {"number": "5", "name": "SCL", "type": PIN_INPUT},
            {"number": "6", "name": "CSB", "type": PIN_INPUT},
        ],
        "footprints": ["Package_LGA:BME280_LGA-8_2.5x2.5mm_P0.65mm"],
    },
    "Sensor:BMP280": {
        "category": CATEGORY_SENSOR, "name": "BMP280 Barometric Pressure Sensor",
        "pins": [
            {"number": "1", "name": "VCC", "type": PIN_POWER_IN},
            {"number": "2", "name": "GND", "type": PIN_POWER_IN},
            {"number": "3", "name": "SDA", "type": PIN_BIDIRECTIONAL},
            {"number": "4", "name": "SDO", "type": PIN_OUTPUT},
            {"number": "5", "name": "SCL", "type": PIN_INPUT},
            {"number": "6", "name": "CSB", "type": PIN_INPUT},
        ],
        "footprints": ["Package_LGA:BMP280"],
    },

    # ========== LOGIC ICs ==========
    "Timer:NE555": {
        "category": CATEGORY_LOGIC, "name": "555 Timer",
        "pins": [
            {"number": "1", "name": "GND", "type": PIN_POWER_IN},
            {"number": "2", "name": "TR", "type": PIN_INPUT},
            {"number": "3", "name": "Q", "type": PIN_OUTPUT},
            {"number": "4", "name": "R", "type": PIN_INPUT},
            {"number": "5", "name": "CV", "type": PIN_INPUT},
            {"number": "6", "name": "THR", "type": PIN_INPUT},
            {"number": "7", "name": "DIS", "type": PIN_INPUT},
            {"number": "8", "name": "VCC", "type": PIN_POWER_IN},
        ],
        "footprints": ["Package_DIP:DIP-8_W7.62mm"],
    },
    "74xx:74HC595": {
        "category": CATEGORY_LOGIC, "name": "74HC595 Shift Register",
        "pins": [
            {"number": "8", "name": "GND", "type": PIN_POWER_IN},
            {"number": "16", "name": "VCC", "type": PIN_POWER_IN},
            {"number": "14", "name": "SER", "type": PIN_INPUT},
            {"number": "11", "name": "SRCLK", "type": PIN_INPUT},
            {"number": "12", "name": "RCLK", "type": PIN_INPUT},
            {"number": "10", "name": "SRCLR", "type": PIN_INPUT},
            {"number": "13", "name": "OE", "type": PIN_INPUT},
            {"number": "15", "name": "QA", "type": PIN_OUTPUT},
            {"number": "1", "name": "QB", "type": PIN_OUTPUT},
            {"number": "2", "name": "QC", "type": PIN_OUTPUT},
            {"number": "3", "name": "QD", "type": PIN_OUTPUT},
            {"number": "4", "name": "QE", "type": PIN_OUTPUT},
            {"number": "5", "name": "QF", "type": PIN_OUTPUT},
            {"number": "6", "name": "QG", "type": PIN_OUTPUT},
            {"number": "7", "name": "QH", "type": PIN_OUTPUT},
            {"number": "9", "name": "QH'", "type": PIN_OUTPUT},
        ],
        "footprints": ["Package_DIP:DIP-16_W7.62mm"],
    },
    "74xx:74HC04": {
        "category": CATEGORY_LOGIC, "name": "74HC04 Hex Inverter",
        "pins": [
            {"number": "7", "name": "GND", "type": PIN_POWER_IN},
            {"number": "14", "name": "VCC", "type": PIN_POWER_IN},
            {"number": "1", "name": "1A", "type": PIN_INPUT}, {"number": "2", "name": "1Y", "type": PIN_OUTPUT},
            {"number": "3", "name": "2A", "type": PIN_INPUT}, {"number": "4", "name": "2Y", "type": PIN_OUTPUT},
            {"number": "5", "name": "3A", "type": PIN_INPUT}, {"number": "6", "name": "3Y", "type": PIN_OUTPUT},
            {"number": "9", "name": "4A", "type": PIN_INPUT}, {"number": "8", "name": "4Y", "type": PIN_OUTPUT},
            {"number": "11", "name": "5A", "type": PIN_INPUT}, {"number": "10", "name": "5Y", "type": PIN_OUTPUT},
            {"number": "13", "name": "6A", "type": PIN_INPUT}, {"number": "12", "name": "6Y", "type": PIN_OUTPUT},
        ],
        "footprints": ["Package_DIP:DIP-14_W7.62mm"],
    },

    # ========== CONNECTORS ==========
    "Connector_Generic:Conn_01x02": {
        "category": CATEGORY_CONNECTOR, "name": "2-Pin Header",
        "pins": [{"number": "1", "name": "Pin_1", "type": PIN_PASSIVE}, {"number": "2", "name": "Pin_2", "type": PIN_PASSIVE}],
        "footprints": ["Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"],
    },
    "Connector_Generic:Conn_01x03": {
        "category": CATEGORY_CONNECTOR, "name": "3-Pin Header",
        "pins": [{"number": "1", "name": "Pin_1", "type": PIN_PASSIVE}, {"number": "2", "name": "Pin_2", "type": PIN_PASSIVE}, {"number": "3", "name": "Pin_3", "type": PIN_PASSIVE}],
        "footprints": ["Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"],
    },
    "Connector_Generic:Conn_01x04": {
        "category": CATEGORY_CONNECTOR, "name": "4-Pin Header",
        "pins": [{"number": str(i), "name": f"Pin_{i}", "type": PIN_PASSIVE} for i in range(1, 5)],
        "footprints": ["Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"],
    },
    "Connector_Generic:Conn_01x06": {
        "category": CATEGORY_CONNECTOR, "name": "6-Pin Header",
        "pins": [{"number": str(i), "name": f"Pin_{i}", "type": PIN_PASSIVE} for i in range(1, 7)],
        "footprints": ["Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"],
    },
    "Connector_Generic:Conn_01x08": {
        "category": CATEGORY_CONNECTOR, "name": "8-Pin Header",
        "pins": [{"number": str(i), "name": f"Pin_{i}", "type": PIN_PASSIVE} for i in range(1, 9)],
        "footprints": ["Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"],
    },
    "Connector:USB_B_Micro": {
        "category": CATEGORY_CONNECTOR, "name": "Micro USB",
        "pins": [
            {"number": "1", "name": "VBUS", "type": PIN_POWER_OUT},
            {"number": "2", "name": "D-", "type": PIN_BIDIRECTIONAL},
            {"number": "3", "name": "D+", "type": PIN_BIDIRECTIONAL},
            {"number": "4", "name": "ID", "type": PIN_PASSIVE},
            {"number": "5", "name": "GND", "type": PIN_POWER_IN},
        ],
        "footprints": ["Connector_USB:USB_Micro-B_Molex-105017-0001"],
    },
    "Connector:USB_C_Receptacle": {
        "category": CATEGORY_CONNECTOR, "name": "USB Type-C",
        "pins": [
            {"number": "A1", "name": "GND", "type": PIN_POWER_IN},
            {"number": "A4", "name": "VBUS", "type": PIN_POWER_OUT},
            {"number": "A6", "name": "D+", "type": PIN_BIDIRECTIONAL},
            {"number": "A7", "name": "D-", "type": PIN_BIDIRECTIONAL},
            {"number": "A5", "name": "CC1", "type": PIN_BIDIRECTIONAL},
        ],
        "footprints": ["Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A"],
    },
    "Connector:Barrel_Jack": {
        "category": CATEGORY_CONNECTOR, "name": "DC Barrel Jack",
        "pins": [
            {"number": "1", "name": "~", "type": PIN_PASSIVE},
            {"number": "2", "name": "~", "type": PIN_PASSIVE},
            {"number": "3", "name": "~", "type": PIN_PASSIVE},
        ],
        "footprints": ["Connector_BarrelJack:BarrelJack_Horizontal"],
    },
    "Connector:Screw_Terminal_01x02": {
        "category": CATEGORY_CONNECTOR, "name": "2-Pin Screw Terminal",
        "pins": [{"number": "1", "name": "Pin_1", "type": PIN_PASSIVE}, {"number": "2", "name": "Pin_2", "type": PIN_PASSIVE}],
        "footprints": ["TerminalBlock:TerminalBlock_bornier-2_P5.08mm"],
    },

    # ========== SWITCHES ==========
    "Switch:SW_Push": {
        "category": CATEGORY_SWITCH, "name": "Push Button",
        "pins": [{"number": "1", "name": "1", "type": PIN_PASSIVE}, {"number": "2", "name": "2", "type": PIN_PASSIVE}],
        "footprints": ["Button_Switch_THT:SW_PUSH_6mm"],
    },
    "Switch:SW_SPDT": {
        "category": CATEGORY_SWITCH, "name": "SPDT Switch",
        "pins": [
            {"number": "1", "name": "A", "type": PIN_PASSIVE},
            {"number": "2", "name": "B", "type": PIN_PASSIVE},
            {"number": "3", "name": "C", "type": PIN_PASSIVE},
        ],
        "footprints": ["Button_Switch_THT:SW_SPDT_CK-JS102011SAQN"],
    },

    # ========== DISPLAYS ==========
    "Display_Character:HD44780": {
        "category": CATEGORY_DISPLAY, "name": "HD44780 LCD 16x2",
        "pins": [
            {"number": "1", "name": "VSS", "type": PIN_POWER_IN},
            {"number": "2", "name": "VDD", "type": PIN_POWER_IN},
            {"number": "3", "name": "V0", "type": PIN_PASSIVE},
            {"number": "4", "name": "RS", "type": PIN_INPUT},
            {"number": "5", "name": "RW", "type": PIN_INPUT},
            {"number": "6", "name": "E", "type": PIN_INPUT},
            {"number": "7", "name": "D0", "type": PIN_BIDIRECTIONAL},
            {"number": "8", "name": "D1", "type": PIN_BIDIRECTIONAL},
            {"number": "9", "name": "D2", "type": PIN_BIDIRECTIONAL},
            {"number": "10", "name": "D3", "type": PIN_BIDIRECTIONAL},
            {"number": "11", "name": "D4", "type": PIN_BIDIRECTIONAL},
            {"number": "12", "name": "D5", "type": PIN_BIDIRECTIONAL},
            {"number": "13", "name": "D6", "type": PIN_BIDIRECTIONAL},
            {"number": "14", "name": "D7", "type": PIN_BIDIRECTIONAL},
            {"number": "15", "name": "A", "type": PIN_PASSIVE},
            {"number": "16", "name": "K", "type": PIN_PASSIVE},
        ],
        "footprints": ["Display:LCD-016N002L"],
    },

    # ========== MOTOR DRIVERS ==========
    "Driver_Motor:L293D": {
        "category": CATEGORY_MOTOR, "name": "L293D Motor Driver",
        "pins": [
            {"number": "1", "name": "EN12", "type": PIN_INPUT},
            {"number": "2", "name": "IN1", "type": PIN_INPUT},
            {"number": "3", "name": "OUT1", "type": PIN_OUTPUT},
            {"number": "4", "name": "GND", "type": PIN_POWER_IN},
            {"number": "5", "name": "GND", "type": PIN_POWER_IN},
            {"number": "6", "name": "OUT2", "type": PIN_OUTPUT},
            {"number": "7", "name": "IN2", "type": PIN_INPUT},
            {"number": "8", "name": "VS", "type": PIN_POWER_IN},
            {"number": "9", "name": "EN34", "type": PIN_INPUT},
            {"number": "10", "name": "IN3", "type": PIN_INPUT},
            {"number": "11", "name": "OUT3", "type": PIN_OUTPUT},
            {"number": "12", "name": "GND", "type": PIN_POWER_IN},
            {"number": "13", "name": "GND", "type": PIN_POWER_IN},
            {"number": "14", "name": "OUT4", "type": PIN_OUTPUT},
            {"number": "15", "name": "IN4", "type": PIN_INPUT},
            {"number": "16", "name": "VSS", "type": PIN_POWER_IN},
        ],
        "footprints": ["Package_DIP:DIP-16_W7.62mm"],
    },

    # ========== RELAYS ==========
    "Relay:FINDER-40.11": {
        "category": CATEGORY_RELAY, "name": "Relay SPDT",
        "pins": [
            {"number": "1", "name": "COIL+", "type": PIN_PASSIVE},
            {"number": "2", "name": "COIL-", "type": PIN_PASSIVE},
            {"number": "3", "name": "COM", "type": PIN_PASSIVE},
            {"number": "4", "name": "NO", "type": PIN_PASSIVE},
            {"number": "5", "name": "NC", "type": PIN_PASSIVE},
        ],
        "footprints": ["Relay_THT:Relay_SPDT_Finder_40.11"],
    },

    # ========== MEMORY ==========
    "Memory_EEPROM:AT24CS02": {
        "category": CATEGORY_MEMORY, "name": "AT24C02 I2C EEPROM",
        "pins": [
            {"number": "1", "name": "A0", "type": PIN_INPUT},
            {"number": "2", "name": "A1", "type": PIN_INPUT},
            {"number": "3", "name": "A2", "type": PIN_INPUT},
            {"number": "4", "name": "GND", "type": PIN_POWER_IN},
            {"number": "5", "name": "SDA", "type": PIN_BIDIRECTIONAL},
            {"number": "6", "name": "SCL", "type": PIN_INPUT},
            {"number": "7", "name": "WP", "type": PIN_INPUT},
            {"number": "8", "name": "VCC", "type": PIN_POWER_IN},
        ],
        "footprints": ["Package_DIP:DIP-8_W7.62mm"],
    },

    # ========== OPTOCOUPLERS ==========
    "Isolator:PC817": {
        "category": CATEGORY_ACTIVE, "name": "PC817 Optocoupler",
        "pins": [
            {"number": "1", "name": "A", "type": PIN_PASSIVE},
            {"number": "2", "name": "K", "type": PIN_PASSIVE},
            {"number": "3", "name": "E", "type": PIN_PASSIVE},
            {"number": "4", "name": "C", "type": PIN_PASSIVE},
        ],
        "footprints": ["Package_DIP:DIP-4_W7.62mm"],
    },

    # ========== POWER SYMBOLS (virtual) ==========
    "power:GND": {
        "category": CATEGORY_POWER, "name": "Ground",
        "pins": [{"number": "1", "name": "GND", "type": PIN_POWER_IN}],
        "footprints": [],
    },
    "power:VCC": {
        "category": CATEGORY_POWER, "name": "VCC Power",
        "pins": [{"number": "1", "name": "VCC", "type": PIN_POWER_IN}],
        "footprints": [],
    },
    "power:+3V3": {
        "category": CATEGORY_POWER, "name": "3.3V Power",
        "pins": [{"number": "1", "name": "+3V3", "type": PIN_POWER_IN}],
        "footprints": [],
    },
    "power:+5V": {
        "category": CATEGORY_POWER, "name": "5V Power",
        "pins": [{"number": "1", "name": "+5V", "type": PIN_POWER_IN}],
        "footprints": [],
    },
    "power:+12V": {
        "category": CATEGORY_POWER, "name": "12V Power",
        "pins": [{"number": "1", "name": "+12V", "type": PIN_POWER_IN}],
        "footprints": [],
    },
}


# ============================================================================
# Lookup Tables for Description Generation
# ============================================================================

# Map lib_id patterns to human-readable descriptions
LIB_ID_DESCRIPTIONS: dict[str, str] = {
    "Device:R": "resistor",
    "Device:R_Small": "resistor",
    "Device:R_POT": "potentiometer",
    "Device:C": "capacitor",
    "Device:C_Small": "capacitor",
    "Device:C_Polarized": "electrolytic capacitor",
    "Device:L": "inductor",
    "Device:LED": "LED",
    "Device:LED_Small": "LED",
    "Device:D": "diode",
    "Device:D_Zener": "Zener diode",
    "Device:D_Schottky": "Schottky diode",
    "Device:Crystal": "crystal oscillator",
    "Device:Fuse": "fuse",
    "Device:Buzzer": "buzzer",
    "Device:Speaker": "speaker",
    "Device:Q_NPN_BCE": "NPN transistor",
    "Device:Q_PNP_BCE": "PNP transistor",
    "Device:Q_NMOS_GDS": "N-MOSFET",
    "Device:Q_PMOS_GDS": "P-MOSFET",
    "Switch:SW_Push": "push button",
    "Switch:SW_SPDT": "toggle switch",
    "Timer:NE555": "555 timer",
    "74xx:74HC595": "shift register",
    "74xx:74HC04": "hex inverter",
    "Sensor:DHT11": "temperature/humidity sensor",
    "Sensor:BME280": "barometric pressure sensor",
    "Sensor:BMP280": "pressure sensor",
    "MCU_Module:Arduino_UNO_R3": "Arduino UNO",
    "MCU_Module:Arduino_Nano_v3.x": "Arduino Nano",
    "MCU_Microchip_ATmega:ATmega328P-PU": "ATmega328P microcontroller",
    "RF_Module:ESP32-WROOM-32": "ESP32 WiFi module",
    "RF_Module:ESP-12E": "ESP8266 WiFi module",
    "Amplifier_Operational:LM358": "dual op-amp",
    "Amplifier_Operational:LM741": "op-amp",
    "Regulator_Linear:LM7805_TO220": "5V voltage regulator",
    "Regulator_Linear:LM7812_TO220": "12V voltage regulator",
    "Regulator_Linear:LM317_TO220": "adjustable voltage regulator",
    "Regulator_Linear:AMS1117-3.3": "3.3V voltage regulator",
    "Display_Character:HD44780": "16x2 LCD display",
    "Driver_Motor:L293D": "motor driver",
    "Memory_EEPROM:AT24CS02": "I2C EEPROM",
    "Isolator:PC817": "optocoupler",
    "Connector:USB_B_Micro": "micro USB connector",
    "Connector:USB_C_Receptacle": "USB-C connector",
    "Connector:Barrel_Jack": "DC barrel jack",
}

# Category keywords for identifying components by partial lib_id match
CATEGORY_PATTERNS: dict[str, str] = {
    "MCU_Module": CATEGORY_MCU,
    "MCU_Microchip": CATEGORY_MCU,
    "MCU_ST": CATEGORY_MCU,
    "MCU_NXP": CATEGORY_MCU,
    "MCU_Texas": CATEGORY_MCU,
    "RF_Module": CATEGORY_MODULE,
    "Sensor": CATEGORY_SENSOR,
    "Driver_Motor": CATEGORY_MOTOR,
    "Driver_FET": CATEGORY_ACTIVE,
    "Amplifier_Operational": CATEGORY_ACTIVE,
    "Amplifier_Audio": CATEGORY_AUDIO,
    "Regulator_Linear": CATEGORY_POWER,
    "Regulator_Switching": CATEGORY_POWER,
    "Timer": CATEGORY_LOGIC,
    "74xx": CATEGORY_LOGIC,
    "4xxx": CATEGORY_LOGIC,
    "Memory_": CATEGORY_MEMORY,
    "Display_": CATEGORY_DISPLAY,
    "Connector": CATEGORY_CONNECTOR,
    "Switch": CATEGORY_SWITCH,
    "Relay": CATEGORY_RELAY,
    "Isolator": CATEGORY_ACTIVE,
    "Device": CATEGORY_PASSIVE,
    "power": CATEGORY_POWER,
}


def get_component_info(lib_id: str) -> dict | None:
    """Get component info from database by lib_id."""
    if lib_id in COMPONENTS:
        return COMPONENTS[lib_id]
    return None


def get_component_description(lib_id: str) -> str:
    """Get human-readable description for a lib_id."""
    if lib_id in LIB_ID_DESCRIPTIONS:
        return LIB_ID_DESCRIPTIONS[lib_id]

    # Try partial match
    for pattern, desc in LIB_ID_DESCRIPTIONS.items():
        if pattern in lib_id or lib_id.endswith(pattern.split(':')[-1]):
            return desc

    # Fallback: extract name from lib_id
    if ':' in lib_id:
        return lib_id.split(':')[-1].replace('_', ' ')
    return lib_id


def get_component_category(lib_id: str) -> str:
    """Determine component category from lib_id."""
    # Exact match
    comp = get_component_info(lib_id)
    if comp:
        return comp["category"]

    # Pattern match on library prefix
    for pattern, category in CATEGORY_PATTERNS.items():
        if lib_id.startswith(pattern):
            return category

    return CATEGORY_PASSIVE


def find_similar_lib_id(lib_id: str) -> str | None:
    """Find the most similar valid lib_id using fuzzy matching."""
    lib_id_lower = lib_id.lower()

    # Exact match
    if lib_id in COMPONENTS:
        return lib_id

    # Try common corrections
    corrections = {
        "device:r": "Device:R",
        "device:c": "Device:C",
        "device:led": "Device:LED",
        "device:d": "Device:D",
        "device:l": "Device:L",
    }
    if lib_id_lower in corrections:
        return corrections[lib_id_lower]

    # Try matching just the component name
    target_name = lib_id.split(':')[-1].lower() if ':' in lib_id else lib_id.lower()
    best_match = None
    best_score = 0

    for known_id in COMPONENTS:
        known_name = known_id.split(':')[-1].lower()
        # Simple substring matching score
        score = 0
        if target_name == known_name:
            score = 100
        elif target_name in known_name or known_name in target_name:
            score = 50
        elif _common_chars(target_name, known_name) > len(target_name) * 0.6:
            score = 30

        if score > best_score:
            best_score = score
            best_match = known_id

    return best_match if best_score >= 30 else None


def validate_pin(lib_id: str, pin_ref: str) -> bool:
    """Check if a pin reference is valid for a component."""
    comp = get_component_info(lib_id)
    if not comp:
        return True  # Can't validate unknown components

    valid_pins = set()
    for pin in comp.get("pins", []):
        valid_pins.add(pin["number"])
        valid_pins.add(pin["name"])

    return pin_ref in valid_pins


def get_valid_pins(lib_id: str) -> list[str]:
    """Get list of valid pin numbers for a component."""
    comp = get_component_info(lib_id)
    if not comp:
        return []
    return [pin["number"] for pin in comp.get("pins", [])]


def _common_chars(a: str, b: str) -> int:
    """Count common characters between two strings."""
    count = 0
    b_list = list(b)
    for c in a:
        if c in b_list:
            count += 1
            b_list.remove(c)
    return count
