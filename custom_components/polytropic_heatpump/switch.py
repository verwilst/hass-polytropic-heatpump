"""Switch platform for Polytropic Heat Pump – unit ON/OFF."""
from __future__ import annotations

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
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
    async_add_entities([PolytropicSwitch(coordinator, entry)])


class PolytropicSwitch(CoordinatorEntity[PolytropicCoordinator], SwitchEntity):
    """Main ON/OFF switch for the heat pump unit."""

    _attr_has_entity_name = True
    _attr_name = "Unit Power"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:heat-pump"

    def __init__(
        self, coordinator: PolytropicCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_unit_power"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Polytropic Heat Pump ({entry.data[CONF_HOST]})",
            "manufacturer": "Polytropic",
            "model": "IVS/IVN",
        }

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get("unit_on")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_turn_on()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_turn_off()
