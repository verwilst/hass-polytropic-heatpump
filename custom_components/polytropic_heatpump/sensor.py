"""Sensor platform for Polytropic Heat Pump."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import PolytropicCoordinator, device_info

DOMAIN = "polytropic_heatpump"


@dataclass(frozen=True)
class PolytropicSensorDescription(SensorEntityDescription):
    coordinator_key: str = ""


SENSOR_DESCRIPTIONS: tuple[PolytropicSensorDescription, ...] = (

    # =========================================================================
    # PRIMARY  – visible on the device card by default
    # =========================================================================

    PolytropicSensorDescription(
        key="water_inlet_temp",
        coordinator_key="water_inlet_temp",
        name="Water Inlet Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    PolytropicSensorDescription(
        key="water_outlet_temp",
        coordinator_key="water_outlet_temp",
        name="Water Outlet Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    PolytropicSensorDescription(
        key="ambient_temp",
        coordinator_key="ambient_temp",
        name="Ambient Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    PolytropicSensorDescription(
        key="delta_t",
        coordinator_key="delta_t",
        name="Delta T Inlet/Outlet",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    PolytropicSensorDescription(
        key="input_power",
        coordinator_key="input_power",
        name="Input Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    PolytropicSensorDescription(
        key="compressor_load",
        coordinator_key="compressor_load",
        name="Compressor Load",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        icon="mdi:gauge",
    ),

    # =========================================================================
    # DIAGNOSTIC  – collapsed under the Diagnostic section in the device card
    # =========================================================================

    PolytropicSensorDescription(
        key="ac_voltage",
        coordinator_key="ac_voltage",
        name="AC Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="ac_current",
        coordinator_key="ac_current",
        name="AC Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="current_freq",
        coordinator_key="current_freq",
        name="Compressor Frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="target_freq",
        coordinator_key="target_freq",
        name="Target Compressor Frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="fan_speed",
        coordinator_key="fan_speed",
        name="Fan Speed 1",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="RPM",
        icon="mdi:fan",
    ),
    PolytropicSensorDescription(
        key="fan_speed_2",
        coordinator_key="fan_speed_2",
        name="Fan Speed 2",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="RPM",
        icon="mdi:fan",
    ),
    PolytropicSensorDescription(
        key="eev2",
        coordinator_key="eev2",
        name="EEV Opening 2",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="steps",
        icon="mdi:valve",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="compressor_op_time",
        coordinator_key="compressor_op_time",
        name="Compressor Operation Time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="failure_code",
        coordinator_key="failure_code",
        name="Compressor Failure Code",
        native_unit_of_measurement=None,
        icon="mdi:alert-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),


    # =========================================================================
    # DIAGNOSTIC – refrigerant circuit temperatures
    # =========================================================================

    PolytropicSensorDescription(
        key="discharge_temp",
        coordinator_key="discharge_temp",
        name="Discharge Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="suction_temp",
        coordinator_key="suction_temp",
        name="Suction Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="coil_temp",
        coordinator_key="coil_temp",
        name="Coil Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="ipm_temp",
        coordinator_key="ipm_temp",
        name="IPM Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    # =========================================================================
    # DIAGNOSTIC – EEV, fan levels, compressor timing
    # =========================================================================

    PolytropicSensorDescription(
        key="eev1",
        coordinator_key="eev1",
        name="EEV Opening 1",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="steps",
        icon="mdi:valve",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="fan_level_1",
        coordinator_key="fan_level_1",
        name="Fan Level 1",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=None,
        icon="mdi:fan",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="fan_level_2",
        coordinator_key="fan_level_2",
        name="Fan Level 2",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=None,
        icon="mdi:fan",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="compressor_stop_time",
        coordinator_key="compressor_stop_time",
        name="Compressor Stop Time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    # =========================================================================
    # DIAGNOSTIC – configuration registers
    # =========================================================================

    PolytropicSensorDescription(
        key="compensation_temp",
        coordinator_key="compensation_temp",
        name="Compensation Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="max_target_temp",
        coordinator_key="max_target_temp",
        name="Max Target Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="circ_pump_mode",
        coordinator_key="circ_pump_mode",
        name="Circulation Pump Mode",
        native_unit_of_measurement=None,
        icon="mdi:pump",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PolytropicSensorDescription(
        key="running_mode",
        coordinator_key="running_mode",
        name="Supported Running Modes",
        native_unit_of_measurement=None,
        icon="mdi:heat-pump",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PolytropicCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PolytropicSensor(coordinator, entry, desc)
        for desc in SENSOR_DESCRIPTIONS
    )


class PolytropicSensor(CoordinatorEntity[PolytropicCoordinator], SensorEntity):
    entity_description: PolytropicSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PolytropicCoordinator,
        entry: ConfigEntry,
        description: PolytropicSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = device_info(entry)

    @property
    def native_value(self) -> Any:
        return self.coordinator.data.get(self.entity_description.coordinator_key)
