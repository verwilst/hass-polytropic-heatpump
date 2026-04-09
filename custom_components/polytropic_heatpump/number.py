"""Number platform for Polytropic Heat Pump – target water temperature."""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import PolytropicCoordinator

DOMAIN = "polytropic_heatpump"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PolytropicCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PolytropicTargetTemp(coordinator, entry)])


class PolytropicTargetTemp(CoordinatorEntity[PolytropicCoordinator], NumberEntity):
    """Number entity to set target water temperature (25-60 °C)."""

    _attr_has_entity_name = True
    _attr_name = "Target Water Temperature"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 25.0
    _attr_native_max_value = 60.0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-water"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, coordinator: PolytropicCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_target_water_temp"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Polytropic Heat Pump ({entry.data[CONF_HOST]})",
            "manufacturer": "Polytropic",
            "model": "IVS/IVN",
        }

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("set_temp")

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_target_temp(value)
