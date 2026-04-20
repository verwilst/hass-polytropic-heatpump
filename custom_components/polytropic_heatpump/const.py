"""
Polytropic heat pump Modbus register map.
Source: Modbus_table_for_IVS_N_.pdf
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Readable configuration registers (low address block, 57–62)
# Note: regs 60 and 61 are undocumented — the vendor docs forbid reading them.
# ---------------------------------------------------------------------------
REG_COMPENSATION_TEMP = 57    # compensation temp setting (-9 to +9 °C), ÷10
REG_MAX_TARGET_TEMP   = 58    # maximum target water temp (25-60 °C), ÷10
REG_CIRC_PUMP_MODE    = 59    # circulation pump mode (0=always on, 1=follow compressor)
REG_RUNNING_MODE      = 62    # supported running modes (0-3)

# ---------------------------------------------------------------------------
# Readable telemetry registers (500–523, contiguous)
# ---------------------------------------------------------------------------
REG_ALARM_500            = 500   # component status bits
REG_ALARM_501            = 501   # sensor faults + protections
REG_ALARM_502            = 502   # electrical / inverter faults
REG_ALARM_503            = 503   # PCB comms, EEPROM, defrost
REG_EEV1                 = 504   # EEV opening 1  (0-500 steps)
REG_EEV2                 = 505   # EEV opening 2  (0-500 steps)
REG_FAN_SPEED            = 506   # fan speed 1    (0-999 RPM)
REG_FAN_SPEED_2          = 507   # fan speed 2    (0-999 RPM)
REG_FAN_LEVEL_1          = 508   # fan speed 1 level (0-3)
REG_FAN_LEVEL_2          = 509   # fan speed 2 level (0-3)
REG_DISCHARGE_TEMP       = 510   # discharge temp, int16 ÷10 = °C
REG_SUCTION_TEMP         = 511   # suction temp,   int16 ÷10 = °C
REG_WATER_INLET          = 512   # int16, ÷10 = °C  range -30..220
REG_WATER_OUTLET         = 513   # int16, ÷10 = °C
REG_COIL_TEMP            = 514   # coil temp,      int16 ÷10 = °C
REG_AMBIENT_TEMP         = 515   # int16, ÷10 = °C
REG_IPM_TEMP             = 516   # IPM temp,       int16 ÷10 = °C
REG_TARGET_FREQ          = 517   # Hz  (0-120)
REG_CURRENT_FREQ         = 518   # Hz  (0-120)
REG_COMPRESSOR_OP_TIME   = 519   # minutes (0-65535)
REG_COMPRESSOR_STOP_TIME = 520   # compressor stop time (minutes)
REG_AC_VOLTAGE           = 521   # volts   (0-500)
REG_AC_CURRENT           = 522   # amps×10 (0-1000 → 0-100 A)
REG_FAILURE_CODE         = 523   # compressor failure code

# ---------------------------------------------------------------------------
# Writable control registers
# ---------------------------------------------------------------------------
REG_CONTROL_WORD = 1000   # Bit0-3: mode (0-7)  Bit4: ON/OFF
REG_SET_TEMP     = 1001   # target water temp × 10  (250-600 → 25-60 °C)

# ---------------------------------------------------------------------------
# Control word bit masks
# ---------------------------------------------------------------------------
CTRL_MODE_MASK = 0x000F   # bits 0-3
CTRL_ON_OFF    = 0x0010   # bit 4

# ---------------------------------------------------------------------------
# Operation modes (REG_CONTROL_WORD bits 0-3)
# ---------------------------------------------------------------------------
MODES: dict[int, str] = {
    0: "standby",
    1: "auto",
    2: "cooling",
    3: "quick_cooling",
    4: "low_noise_cooling",
    5: "heating",
    6: "quick_heating",
    7: "low_noise_heating",
}

MODE_NAMES: dict[int, str] = {
    0: "Standby",
    1: "Auto",
    2: "Cooling",
    3: "Quick Cooling",
    4: "Low Noise Cooling",
    5: "Heating",
    6: "Quick Heating",
    7: "Low Noise Heating",
}

# ---------------------------------------------------------------------------
# Bit definitions – word 500 (component status)
# ---------------------------------------------------------------------------
BIT500_HIGH_PRESSURE_SWITCH  = 0x0001
BIT500_LOW_PRESSURE_SWITCH   = 0x0002
BIT500_WATER_FLOW_SWITCH     = 0x0008
BIT500_WATER_PUMP            = 0x0020
BIT500_ELECTRIC_HEATER       = 0x0040
BIT500_FOUR_WAY_VALVE        = 0x0080
BIT500_BOTTOM_PLATE_HEATER   = 0x0100
BIT500_COMPRESSOR_HEATER     = 0x0200

# ---------------------------------------------------------------------------
# Bit definitions – word 501 (sensor faults / protections)
# ---------------------------------------------------------------------------
BIT501_FAULT_WATER_INLET     = 0x0001  # AL03
BIT501_FAULT_WATER_OUTLET    = 0x0002  # AL04
BIT501_FAULT_COIL            = 0x0004  # AL05
BIT501_FAULT_AMBIENT         = 0x0008  # AL06
BIT501_PROT_AMBIENT_LOW      = 0x0010  # AL14
BIT501_FAULT_DISCHARGE       = 0x0020  # AL01
BIT501_FAULT_SUCTION         = 0x0040  # AL02
BIT501_PROT_DELTA_T_HIGH     = 0x0080  # AL15
BIT501_PROT_DELTA_T_HIGH_3X  = 0x0100  # AL16
BIT501_PROT_OVERCOOL         = 0x0200  # AL17
BIT501_PROT_HIGH_PRESSURE    = 0x0400  # AL10
BIT501_PROT_HIGH_PRESS_3X    = 0x0800  # AL11
BIT501_PROT_LOW_PRESSURE     = 0x1000  # AL12
BIT501_PROT_LOW_PRESS_3X     = 0x2000  # AL13
BIT501_PROT_WATER_FLOW       = 0x4000  # FLO
BIT501_PROT_ANTIFREEZE       = 0x8000

# ---------------------------------------------------------------------------
# Bit definitions – word 502 (electrical / inverter)
# ---------------------------------------------------------------------------
BIT502_FAULT_DISCHARGE_HIGH  = 0x0001  # AL18
BIT502_FAULT_AC_VOLTAGE      = 0x0002  # AL19
BIT502_FAULT_DC_CURRENT      = 0x0004  # AL21
BIT502_FAULT_AC_CURRENT      = 0x0008  # AL20
BIT502_FAULT_COMP_OVERCURR   = 0x0010  # AL22
BIT502_FAULT_IPM_OVERHEAT    = 0x0020  # AL23
BIT502_FAULT_IPM             = 0x0040  # AL24
BIT502_FAULT_COMP_DRIVER     = 0x0080  # AL25
BIT502_FAULT_FAN1            = 0x0100  # AL09
BIT502_FAULT_DRIVER_COMMS    = 0x0400  # EA07

# ---------------------------------------------------------------------------
# Bit definitions – word 503 (PCB comms / defrost)
# ---------------------------------------------------------------------------
BIT503_FAULT_MAIN_PCB_COMMS  = 0x0001  # AL07
BIT503_FAULT_EEPROM          = 0x0002  # AL08
BIT503_DEFROST               = 0x8000

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------
CONF_DEBUG = "debug_logging"

DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL     = 15
MAX_SCAN_INTERVAL     = 900