"""Select platform for Polytropic Heat Pump – operation mode."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import PolytropicCoordinator
from .const import MODE_NAMES

DOMAIN = "polytropic_heatpump"

# Inverse lookup: "Heating" → 5
MODE_IDS: dict[str, int] = {v: k for k, v in MODE_NAMES.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PolytropicCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PolytropicModeSelect(coordinator, entry)])


class PolytropicModeSelect(CoordinatorEntity[PolytropicCoordinator], SelectEntity):
    """Select entity for heat pump operating mode."""

    _attr_has_entity_name = True
    _attr_name = "Operating Mode"
    _attr_icon = "mdi:heat-pump"
    _attr_options = list(MODE_NAMES.values())

    def __init__(
        self, coordinator: PolytropicCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_operating_mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Polytropic Heat Pump ({entry.data[CONF_HOST]})",
            "manufacturer": "Polytropic",
            "model": "IVS/IVN",
        }

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data.get("mode_name")

    async def async_select_option(self, option: str) -> None:
        mode_id = MODE_IDS.get(option)
        if mode_id is not None:
            await self.coordinator.async_set_mode(mode_id)
