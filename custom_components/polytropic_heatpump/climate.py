"""Climate platform for Polytropic Heat Pump."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import PolytropicCoordinator

DOMAIN = "polytropic_heatpump"

# Preset names
PRESET_NORMAL     = "Normal"
PRESET_BOOST      = "Boost"
PRESET_SILENT     = "Silent"

# mode_id → (HVACMode, preset)
MODE_ID_TO_HVAC_PRESET: dict[int, tuple[HVACMode, str]] = {
    0: (HVACMode.OFF,  PRESET_NORMAL),
    1: (HVACMode.AUTO, PRESET_NORMAL),
    2: (HVACMode.COOL, PRESET_NORMAL),
    3: (HVACMode.COOL, PRESET_BOOST),   # quick cooling
    4: (HVACMode.COOL, PRESET_SILENT),  # low noise cooling
    5: (HVACMode.HEAT, PRESET_NORMAL),
    6: (HVACMode.HEAT, PRESET_BOOST),   # quick heating
    7: (HVACMode.HEAT, PRESET_SILENT),  # low noise heating
}

# (HVACMode, preset) → mode_id
HVAC_PRESET_TO_MODE_ID: dict[tuple[HVACMode, str], int] = {
    v: k for k, v in MODE_ID_TO_HVAC_PRESET.items()
    if v[0] != HVACMode.OFF  # OFF has no preset concept
}

# When switching HVAC mode without changing preset, use this default mode_id
HVAC_DEFAULT_MODE_ID: dict[HVACMode, int] = {
    HVACMode.HEAT: 5,
    HVACMode.COOL: 2,
    HVACMode.AUTO: 1,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PolytropicCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PolytropicClimate(coordinator, entry)])


class PolytropicClimate(CoordinatorEntity[PolytropicCoordinator], ClimateEntity):
    """Climate entity for the Polytropic heat pump."""

    _attr_has_entity_name = True
    _attr_name = "Climate"
    _attr_icon = "mdi:heat-pump"

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 25.0
    _attr_max_temp = 60.0
    _attr_target_temperature_step = 0.5

    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.AUTO,
    ]
    _attr_preset_modes = [PRESET_NORMAL, PRESET_BOOST, PRESET_SILENT]

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(
        self, coordinator: PolytropicCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Polytropic Heat Pump ({entry.data[CONF_HOST]})",
            "manufacturer": "Polytropic",
            "model": "IVS/IVN",
        }

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def _mode_id(self) -> int:
        return self.coordinator.data.get("mode_id", 0)

    @property
    def hvac_mode(self) -> HVACMode:
        if not self.coordinator.data.get("unit_on", False):
            return HVACMode.OFF
        hvac, _ = MODE_ID_TO_HVAC_PRESET.get(self._mode_id(), (HVACMode.OFF, PRESET_NORMAL))
        return hvac

    @property
    def preset_mode(self) -> str:
        _, preset = MODE_ID_TO_HVAC_PRESET.get(self._mode_id(), (HVACMode.HEAT, PRESET_NORMAL))
        return preset

    @property
    def hvac_action(self) -> HVACAction | None:
        if not self.coordinator.data.get("unit_on", False):
            return HVACAction.OFF
        if self.coordinator.data.get("defrost_active"):
            return HVACAction.DEFROSTING
        freq = self.coordinator.data.get("current_freq", 0)
        if freq == 0:
            return HVACAction.IDLE
        mode = self.hvac_mode
        if mode == HVACMode.HEAT:
            return HVACAction.HEATING
        if mode == HVACMode.COOL:
            return HVACAction.COOLING
        return HVACAction.IDLE

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.get("water_inlet_temp")

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data.get("set_temp")

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_turn_off()
        else:
            # Keep current preset when switching mode
            current_preset = self.preset_mode
            mode_id = HVAC_PRESET_TO_MODE_ID.get(
                (hvac_mode, current_preset),
                HVAC_DEFAULT_MODE_ID.get(hvac_mode, 5),
            )
            await self.coordinator.async_set_mode(mode_id)
            if not self.coordinator.data.get("unit_on", False):
                await self.coordinator.async_turn_on()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        # Keep current HVAC mode when switching preset
        current_hvac = self.hvac_mode
        if current_hvac == HVACMode.OFF:
            return
        mode_id = HVAC_PRESET_TO_MODE_ID.get(
            (current_hvac, preset_mode),
            HVAC_DEFAULT_MODE_ID.get(current_hvac, 5),
        )
        await self.coordinator.async_set_mode(mode_id)

    async def async_set_temperature(self, **kwargs) -> None:
        temp = kwargs.get("temperature")
        if temp is not None:
            await self.coordinator.async_set_target_temp(float(temp))

    async def async_turn_on(self) -> None:
        await self.coordinator.async_turn_on()

    async def async_turn_off(self) -> None:
        await self.coordinator.async_turn_off()
