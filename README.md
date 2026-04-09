# Polytropic Heat Pump - HomeAssistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Codeberg release](https://img.shields.io/gitea/v/release/verwilst/hass-polytropic-heatpump?gitea_url=https://codeberg.org)](https://codeberg.org/verwilst/hass-polytropic-heatpump/releases)
[![Codeberg stars](https://img.shields.io/gitea/stars/verwilst/hass-polytropic-heatpump?gitea_url=https://codeberg.org)](https://codeberg.org/verwilst/hass-polytropic-heatpump)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-donate-yellow.svg)](https://www.buymeacoffee.com/verwilst)

Home Assistant custom integration for Polytropic IVS/IVN heat pumps via Modbus RTU over TCP.

## Tested hardware

- **Heat pump**: Blueplus 17kW Full Inverter (a rebranded Polytropic IVS/IVN)
- **Gateway**: Waveshare RS485-to-ETH/WiFi serial server

## Requirements

- A Modbus RTU over TCP gateway connected to the heat pump's RS485 port (A+, B-, GND)
- Home Assistant 2023.1.0 or newer

## Installation via HACS

1. In HACS, go to **Integrations** → **⋮** → **Custom repositories**
2. Add https://codeberg.org/verwilst/hass-polytropic-heatpump, category: **Integration**
3. Install **Polytropic Heat Pump**
4. Restart Home Assistant
5. Go to **Settings → Integrations → Add Integration** and search for **Polytropic Heat Pump**

## Manual installation

Copy the `custom_components/polytropic_heatpump/` folder into your HA config directory and restart.

## Configuration

| Field | Description | Default |
|-------|-------------|---------|
| Host / IP | IP address of your Modbus TCP gateway | — |
| TCP port | TCP port of the gateway | 8899 |
| Modbus slave address | Slave address set via DIP switches on the PCB (SW1) | 17 |

The default slave address is 17 (all DIP switches OFF).

## Entities

### Climate
- HVAC modes: Heat, Cool, Auto, Off
- Presets: Normal, Boost (quick), Silent (low noise)
- Target water temperature setpoint (25–60 °C)

### Primary sensors
| Entity | Description |
|--------|-------------|
| Water Inlet Temperature | Water temperature entering the heat pump |
| Water Outlet Temperature | Water temperature leaving the heat pump |
| Ambient Temperature | Outdoor air temperature |
| Delta T Inlet/Outlet | Temperature difference between inlet and outlet |
| Input Power | Electrical power consumption (V × A) |
| Compressor Load | Compressor load as percentage of max frequency |
| Fan Speed 1 | Fan 1 speed in RPM |
| Fan Speed 2 | Fan 2 speed in RPM |

### Primary binary sensors
| Entity | Description |
|--------|-------------|
| Water Pump Running | Circulation pump active |
| Electric Heater | Auxiliary electric heater active |
| Bottom Plate Heater | Bottom plate frost heater active |
| Compressor Heater | Compressor crankcase heater active |
| Defrost Active | Defrost cycle in progress |

### Diagnostic sensors
| Entity | Description |
|--------|-------------|
| AC Voltage | Supply voltage |
| AC Current | Supply current |
| Compressor Frequency | Current compressor frequency (Hz) |
| Target Compressor Frequency | Target compressor frequency (Hz) |
| EEV Opening 1 / 2 | Electronic expansion valve positions |
| Fan Level 1 / 2 | Fan speed levels (0–3) |
| Compressor Operation Time | Total compressor running time (minutes) |
| Compressor Stop Time | Total compressor stop time (minutes) |
| Compressor Failure Code | Fault code from compressor driver |
| Discharge Temperature | Refrigerant discharge temperature |
| Suction Temperature | Refrigerant suction temperature |
| Coil Temperature | Heat exchanger coil temperature |
| IPM Temperature | Inverter power module temperature |
| Compensation Temperature | Configured temperature compensation offset |
| Max Target Water Temperature | Configured maximum water temperature |
| Circulation Pump Mode | Pump follow mode (0=always on, 1=follow compressor) |
| Supported Running Modes | Unit running mode capability |

### Diagnostic binary sensors — status flags
| Entity | Description |
|--------|-------------|
| High Pressure Switch | High pressure circuit switch state |
| Low Pressure Switch | Low pressure circuit switch state |
| Water Flow Switch | Water flow switch state |
| Four Way Valve | Reversing valve state (cooling/heating direction) |

### Diagnostic binary sensors — faults & protections
| Entity | AL Code | Description |
|--------|---------|-------------|
| Fault: Discharge Temp Sensor | AL01 | Discharge temperature sensor failure |
| Fault: Suction Temp Sensor | AL02 | Suction temperature sensor failure |
| Fault: Water Inlet Temp Sensor | AL03 | Water inlet temperature sensor failure |
| Fault: Water Outlet Temp Sensor | AL04 | Water outlet temperature sensor failure |
| Fault: Coil Temp Sensor | AL05 | Coil temperature sensor failure |
| Fault: Ambient Temp Sensor | AL06 | Ambient temperature sensor failure |
| Fault: Main PCB Communication | AL07 | Main PCB communication failure |
| Fault: EEPROM Read Error | AL08 | EEPROM data read error |
| Fault: DC Fan Motor 1 | AL09 | DC fan motor 1 failure |
| Protection: High Pressure | AL10 | High pressure switch protection |
| Protection: High Pressure ×3 | AL11 | High pressure protection triggered 3 times |
| Protection: Low Pressure | AL12 | Low pressure switch protection |
| Protection: Low Pressure ×3 | AL13 | Low pressure protection triggered 3 times |
| Protection: Ambient Too Low | AL14 | Ambient temperature too low protection |
| Protection: Delta T Too High | AL15 | Inlet/outlet temperature difference too high |
| Protection: Delta T Too High x3 | AL16 | Delta T protection triggered 3 times |
| Protection: Overcool | AL17 | Cooling overcool protection |
| Fault: Discharge Temp Too High | AL18 | Discharge temperature too high |
| Fault: AC Voltage Input | AL19 | AC voltage input protection |
| Fault: AC Current Input | AL20 | AC current input protection |
| Fault: DC Main Line Current | AL21 | DC main line current protection |
| Fault: Compressor Over-Current | AL22 | Compressor over-current protection |
| Fault: IPM Overheat | AL23 | IPM temperature overheat protection |
| Fault: IPM | AL24 | IPM protection |
| Fault: Compressor Driver | AL25 | Compressor driver protection |
| Protection: Water Flow | FLO | Water flow switch protection |
| Fault: Driver PCB Communication | EA07 | Driver PCB communication failure |
| Protection: Anti-Freeze | — | Anti-freeze protection active |

## Poll interval

All registers are polled every 60 seconds in a single TCP session.

## Modbus address (DIP switches)

The default address is 17 (all switches OFF). See the PCB label (SW1) to change it.
