"""Polytropic Heat Pump integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SLAVE, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_DEBUG
from .coordinator import PolytropicCoordinator

_LOGGER = logging.getLogger(__name__)
_INTEGRATION_LOGGER = logging.getLogger("custom_components.polytropic_heatpump")

DOMAIN = "polytropic_heatpump"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Polytropic HP from a config entry."""
    if entry.options.get(CONF_DEBUG, False):
        _INTEGRATION_LOGGER.setLevel(logging.DEBUG)
        _LOGGER.debug("Debug logging enabled")
    else:
        _INTEGRATION_LOGGER.setLevel(logging.NOTSET)

    coordinator = PolytropicCoordinator(
        hass=hass,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        slave=entry.data[CONF_SLAVE],
    )

    # Initial data fetch – raises ConfigEntryNotReady on failure
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
