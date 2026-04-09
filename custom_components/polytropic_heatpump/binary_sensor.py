"""Binary sensor platform for Polytropic Heat Pump."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import PolytropicCoordinator
from .const import (
    BIT500_HIGH_PRESSURE_SWITCH, BIT500_LOW_PRESSURE_SWITCH,
    BIT500_WATER_FLOW_SWITCH, BIT500_WATER_PUMP,
    BIT500_ELECTRIC_HEATER, BIT500_FOUR_WAY_VALVE,
    BIT500_BOTTOM_PLATE_HEATER, BIT500_COMPRESSOR_HEATER,
    BIT501_FAULT_WATER_INLET, BIT501_FAULT_WATER_OUTLET,
    BIT501_FAULT_COIL, BIT501_FAULT_AMBIENT,
    BIT501_PROT_AMBIENT_LOW, BIT501_FAULT_DISCHARGE,
    BIT501_FAULT_SUCTION, BIT501_PROT_DELTA_T_HIGH,
    BIT501_PROT_DELTA_T_HIGH_3X, BIT501_PROT_OVERCOOL,
    BIT501_PROT_HIGH_PRESSURE, BIT501_PROT_HIGH_PRESS_3X,
    BIT501_PROT_LOW_PRESSURE, BIT501_PROT_LOW_PRESS_3X,
    BIT501_PROT_WATER_FLOW, BIT501_PROT_ANTIFREEZE,
    BIT502_FAULT_DISCHARGE_HIGH, BIT502_FAULT_AC_VOLTAGE,
    BIT502_FAULT_DC_CURRENT, BIT502_FAULT_AC_CURRENT,
    BIT502_FAULT_COMP_OVERCURR, BIT502_FAULT_IPM_OVERHEAT,
    BIT502_FAULT_IPM, BIT502_FAULT_COMP_DRIVER,
    BIT502_FAULT_FAN1, BIT502_FAULT_DRIVER_COMMS,
    BIT503_FAULT_MAIN_PCB_COMMS, BIT503_FAULT_EEPROM,
    BIT503_DEFROST,
)

DOMAIN = "polytropic_heatpump"


@dataclass(frozen=True)
class PolytropicBinarySensorDescription(BinarySensorEntityDescription):
    word_key: str = ""    # which alarm_NNN key in coordinator.data
    bit_mask: int = 0


BINARY_SENSOR_DESCRIPTIONS: tuple[PolytropicBinarySensorDescription, ...] = (
    # -----------------------------------------------------------------------
    # Word 500 – component status
    # -----------------------------------------------------------------------
    PolytropicBinarySensorDescription(
        key="high_pressure_switch",
        name="High Pressure Switch",
        device_class=BinarySensorDeviceClass.RUNNING,
        word_key="alarm_500", bit_mask=BIT500_HIGH_PRESSURE_SWITCH,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="low_pressure_switch",
        name="Low Pressure Switch",
        device_class=BinarySensorDeviceClass.RUNNING,
        word_key="alarm_500", bit_mask=BIT500_LOW_PRESSURE_SWITCH,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="water_flow_switch",
        name="Water Flow Switch",
        device_class=BinarySensorDeviceClass.RUNNING,
        word_key="alarm_500", bit_mask=BIT500_WATER_FLOW_SWITCH,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="water_pump_running",
        name="Water Pump Running",
        device_class=BinarySensorDeviceClass.RUNNING,
        word_key="alarm_500", bit_mask=BIT500_WATER_PUMP,
    ),
    PolytropicBinarySensorDescription(
        key="electric_heater",
        name="Electric Heater",
        device_class=BinarySensorDeviceClass.HEAT,
        word_key="alarm_500", bit_mask=BIT500_ELECTRIC_HEATER,
    ),
    PolytropicBinarySensorDescription(
        key="four_way_valve",
        name="Four Way Valve",
        word_key="alarm_500", bit_mask=BIT500_FOUR_WAY_VALVE,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:valve",
    ),
    PolytropicBinarySensorDescription(
        key="bottom_plate_heater",
        name="Bottom Plate Heater",
        device_class=BinarySensorDeviceClass.HEAT,
        word_key="alarm_500", bit_mask=BIT500_BOTTOM_PLATE_HEATER,
    ),
    PolytropicBinarySensorDescription(
        key="compressor_heater",
        name="Compressor Heater",
        device_class=BinarySensorDeviceClass.HEAT,
        word_key="alarm_500", bit_mask=BIT500_COMPRESSOR_HEATER,
    ),

    # -----------------------------------------------------------------------
    # Word 501 – sensor faults + protections
    # -----------------------------------------------------------------------
    PolytropicBinarySensorDescription(
        key="fault_water_inlet_sensor",
        name="Fault: Water Inlet Temp Sensor (AL03)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_FAULT_WATER_INLET,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_water_outlet_sensor",
        name="Fault: Water Outlet Temp Sensor (AL04)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_FAULT_WATER_OUTLET,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_coil_sensor",
        name="Fault: Coil Temp Sensor (AL05)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_FAULT_COIL,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_ambient_sensor",
        name="Fault: Ambient Temp Sensor (AL06)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_FAULT_AMBIENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="prot_ambient_too_low",
        name="Protection: Ambient Too Low (AL14)",
        device_class=BinarySensorDeviceClass.COLD,
        word_key="alarm_501", bit_mask=BIT501_PROT_AMBIENT_LOW,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_discharge_sensor",
        name="Fault: Discharge Temp Sensor (AL01)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_FAULT_DISCHARGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_suction_sensor",
        name="Fault: Suction Temp Sensor (AL02)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_FAULT_SUCTION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="prot_delta_t_high",
        name="Protection: Delta T Too High (AL15)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_PROT_DELTA_T_HIGH,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="prot_delta_t_high_3x",
        name="Protection: Delta T Too High x3 (AL16)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_PROT_DELTA_T_HIGH_3X,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="prot_overcool",
        name="Protection: Overcool (AL17)",
        device_class=BinarySensorDeviceClass.COLD,
        word_key="alarm_501", bit_mask=BIT501_PROT_OVERCOOL,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="prot_high_pressure",
        name="Protection: High Pressure (AL10)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_PROT_HIGH_PRESSURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="prot_high_pressure_3x",
        name="Protection: High Pressure ×3 (AL11)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_PROT_HIGH_PRESS_3X,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="prot_low_pressure",
        name="Protection: Low Pressure (AL12)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_PROT_LOW_PRESSURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="prot_low_pressure_3x",
        name="Protection: Low Pressure ×3 (AL13)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_PROT_LOW_PRESS_3X,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="prot_water_flow",
        name="Protection: Water Flow (FLO)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_501", bit_mask=BIT501_PROT_WATER_FLOW,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="prot_antifreeze",
        name="Protection: Anti-Freeze",
        device_class=BinarySensorDeviceClass.COLD,
        word_key="alarm_501", bit_mask=BIT501_PROT_ANTIFREEZE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    # -----------------------------------------------------------------------
    # Word 502 – electrical / inverter faults
    # -----------------------------------------------------------------------
    PolytropicBinarySensorDescription(
        key="fault_discharge_temp_high",
        name="Fault: Discharge Temp Too High (AL18)",
        device_class=BinarySensorDeviceClass.HEAT,
        word_key="alarm_502", bit_mask=BIT502_FAULT_DISCHARGE_HIGH,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_ac_voltage",
        name="Fault: AC Voltage Input (AL19)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_502", bit_mask=BIT502_FAULT_AC_VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_dc_current",
        name="Fault: DC Main Line Current (AL21)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_502", bit_mask=BIT502_FAULT_DC_CURRENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_ac_current",
        name="Fault: AC Current Input (AL20)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_502", bit_mask=BIT502_FAULT_AC_CURRENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_compressor_overcurrent",
        name="Fault: Compressor Over-Current (AL22)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_502", bit_mask=BIT502_FAULT_COMP_OVERCURR,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_ipm_overheat",
        name="Fault: IPM Overheat (AL23)",
        device_class=BinarySensorDeviceClass.HEAT,
        word_key="alarm_502", bit_mask=BIT502_FAULT_IPM_OVERHEAT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_ipm",
        name="Fault: IPM (AL24)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_502", bit_mask=BIT502_FAULT_IPM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_compressor_driver",
        name="Fault: Compressor Driver (AL25)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_502", bit_mask=BIT502_FAULT_COMP_DRIVER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_fan_motor_1",
        name="Fault: DC Fan Motor 1 (AL09)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_502", bit_mask=BIT502_FAULT_FAN1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_driver_comms",
        name="Fault: Driver PCB Communication (EA07)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_502", bit_mask=BIT502_FAULT_DRIVER_COMMS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    # -----------------------------------------------------------------------
    # Word 503 – PCB comms / EEPROM / defrost
    # -----------------------------------------------------------------------
    PolytropicBinarySensorDescription(
        key="fault_main_pcb_comms",
        name="Fault: Main PCB Communication (AL07)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_503", bit_mask=BIT503_FAULT_MAIN_PCB_COMMS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="fault_eeprom",
        name="Fault: EEPROM Read Error (AL08)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        word_key="alarm_503", bit_mask=BIT503_FAULT_EEPROM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicBinarySensorDescription(
        key="defrost_active",
        name="Defrost Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        word_key="alarm_503", bit_mask=BIT503_DEFROST,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:snowflake-melt",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PolytropicCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PolytropicBinarySensor(coordinator, entry, desc)
        for desc in BINARY_SENSOR_DESCRIPTIONS
    )


class PolytropicBinarySensor(
    CoordinatorEntity[PolytropicCoordinator], BinarySensorEntity
):
    entity_description: PolytropicBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PolytropicCoordinator,
        entry: ConfigEntry,
        description: PolytropicBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Polytropic Heat Pump ({entry.data[CONF_HOST]})",
            "manufacturer": "Polytropic",
            "model": "IVS/IVN",
        }

    @property
    def is_on(self) -> bool | None:
        word = self.coordinator.data.get(self.entity_description.word_key)
        if word is None:
            return None
        return bool(word & self.entity_description.bit_mask)
