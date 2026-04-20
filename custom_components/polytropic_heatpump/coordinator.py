"""
DataUpdateCoordinator for Polytropic heat pump.

Polls all registers every 60 seconds in a single TCP session using four
batched FC 0x03 reads (grouped around the gap at regs 60-61 — the vendor
docs forbid touching undocumented addresses).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    REG_ALARM_500, REG_ALARM_501, REG_ALARM_502, REG_ALARM_503,
    REG_EEV1, REG_EEV2, REG_FAN_SPEED, REG_FAN_SPEED_2,
    REG_FAN_LEVEL_1, REG_FAN_LEVEL_2,
    REG_DISCHARGE_TEMP, REG_SUCTION_TEMP, REG_COIL_TEMP, REG_IPM_TEMP,
    REG_COMPRESSOR_STOP_TIME,
    REG_COMPENSATION_TEMP, REG_MAX_TARGET_TEMP, REG_CIRC_PUMP_MODE, REG_RUNNING_MODE,
    REG_WATER_INLET, REG_WATER_OUTLET, REG_AMBIENT_TEMP,
    REG_TARGET_FREQ, REG_CURRENT_FREQ,
    REG_COMPRESSOR_OP_TIME,
    REG_AC_VOLTAGE, REG_AC_CURRENT,
    REG_FAILURE_CODE,
    REG_CONTROL_WORD, REG_SET_TEMP,
    CTRL_MODE_MASK, CTRL_ON_OFF,
)
from .modbus_client import ModbusRTUClient, ModbusError

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)

DOMAIN = "polytropic_heatpump"


def _to_signed(v: int) -> int:
    """Interpret a uint16 as a two's-complement int16."""
    return v if v < 0x8000 else v - 0x10000


class PolytropicCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll all registers every 60 s in a single TCP session."""

    def __init__(
            self,
            hass: HomeAssistant,
            host: str,
            port: int,
            slave: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self._client = ModbusRTUClient(
            host=host,
            port=port,
            slave=slave,
            inter_request_delay=0.1,
            timeout=5.0,
        )
        self._cached: dict[str, Any] = {
            "set_temp": 35.0,   # sensible default until first poll
        }
        self._bus_lock = asyncio.Lock()  # serialise poll + write access

    # ------------------------------------------------------------------
    # Poll
    # ------------------------------------------------------------------

    async def _poll_all(self) -> dict[str, Any]:
        """Read every register in four batched FC 0x03 requests."""
        # Block A: regs 57-59 (compensation, max target, pump mode)
        block_a = await self._client.read_holding_registers(REG_COMPENSATION_TEMP, 3)
        # Reg 62 (running mode) — isolated; regs 60-61 are undocumented, never touch
        running_mode = await self._client.read_holding_register(REG_RUNNING_MODE)
        # Block B: regs 500-523 (alarms + full telemetry, all documented)
        block_b = await self._client.read_holding_registers(REG_ALARM_500, 24)
        # Block C: regs 1000-1001 (control word + setpoint)
        block_c = await self._client.read_holding_registers(REG_CONTROL_WORD, 2)

        def _a(reg: int) -> int:
            return block_a[reg - REG_COMPENSATION_TEMP]

        def _b(reg: int) -> int:
            return block_b[reg - REG_ALARM_500]

        ctrl = block_c[0]
        data: dict[str, Any] = {
            # --- Block A ---
            "compensation_temp_raw": _to_signed(_a(REG_COMPENSATION_TEMP)),
            "max_target_temp_raw":   _a(REG_MAX_TARGET_TEMP),
            "circ_pump_mode":        _a(REG_CIRC_PUMP_MODE),
            "running_mode":          running_mode,

            # --- Block B: alarms ---
            "alarm_500": _b(REG_ALARM_500),
            "alarm_501": _b(REG_ALARM_501),
            "alarm_502": _b(REG_ALARM_502),
            "alarm_503": _b(REG_ALARM_503),

            # --- Block B: EEV / fan ---
            "eev1":        _b(REG_EEV1),
            "eev2":        _b(REG_EEV2),
            "fan_speed":   _b(REG_FAN_SPEED),
            "fan_speed_2": _b(REG_FAN_SPEED_2),
            "fan_level_1": _b(REG_FAN_LEVEL_1),
            "fan_level_2": _b(REG_FAN_LEVEL_2),

            # --- Block B: refrigerant / water / ambient (signed) ---
            "discharge_temp_raw": _to_signed(_b(REG_DISCHARGE_TEMP)),
            "suction_temp_raw":   _to_signed(_b(REG_SUCTION_TEMP)),
            "water_inlet_raw":    _to_signed(_b(REG_WATER_INLET)),
            "water_outlet_raw":   _to_signed(_b(REG_WATER_OUTLET)),
            "coil_temp_raw":      _to_signed(_b(REG_COIL_TEMP)),
            "ambient_raw":        _to_signed(_b(REG_AMBIENT_TEMP)),
            "ipm_temp_raw":       _to_signed(_b(REG_IPM_TEMP)),

            # --- Block B: frequency / times / electrical / failure ---
            "target_freq":          _b(REG_TARGET_FREQ),
            "current_freq":         _b(REG_CURRENT_FREQ),
            "compressor_op_time":   _b(REG_COMPRESSOR_OP_TIME),
            "compressor_stop_time": _b(REG_COMPRESSOR_STOP_TIME),
            "ac_voltage_raw":       _b(REG_AC_VOLTAGE),
            "ac_current_raw":       _b(REG_AC_CURRENT),
            "failure_code":         _b(REG_FAILURE_CODE),

            # --- Block C: control word + setpoint ---
            "control_word": ctrl,
            "unit_on":      bool(ctrl & CTRL_ON_OFF),
            "mode_id":      ctrl & CTRL_MODE_MASK,
            "set_temp_raw": block_c[1],
        }

        # Derived values
        water_inlet  = max(-30.0, min(220.0, data["water_inlet_raw"]  / 10))
        water_outlet = max(-30.0, min(220.0, data["water_outlet_raw"] / 10))
        ambient      = max(-30.0, min(220.0, data["ambient_raw"]      / 10))

        data["water_inlet_temp"]  = round(water_inlet,  1)
        data["water_outlet_temp"] = round(water_outlet, 1)
        data["ambient_temp"]      = round(ambient,       1)
        data["set_temp"]          = round(max(25.0, min(60.0, data["set_temp_raw"] / 10)), 1)

        data["ac_voltage"] = min(500, max(0, data["ac_voltage_raw"]))
        data["ac_current"] = round(min(100.0, max(0.0, data["ac_current_raw"] / 10)), 1)

        data["input_power"] = round(data["ac_voltage"] * data["ac_current"], 0)

        freq = min(120, max(0, data["current_freq"]))
        data["compressor_load"] = int(freq / 120 * 100)
        data["delta_t"]         = round(water_outlet - water_inlet, 1)

        data["discharge_temp"]    = round(max(-30.0, min(220.0, data["discharge_temp_raw"] / 10)), 1)
        data["suction_temp"]      = round(max(-30.0, min(220.0, data["suction_temp_raw"]   / 10)), 1)
        data["coil_temp"]         = round(max(-30.0, min(220.0, data["coil_temp_raw"]      / 10)), 1)
        data["ipm_temp"]          = round(max(-30.0, min(220.0, data["ipm_temp_raw"]       / 10)), 1)
        data["compensation_temp"] = round(data["compensation_temp_raw"] / 10, 1)
        data["max_target_temp"]   = round(max(25.0, min(60.0, data["max_target_temp_raw"] / 10)), 1)

        return data

    # ------------------------------------------------------------------
    # DataUpdateCoordinator override
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            async with self._bus_lock:
                async with self._client:
                    data = await self._poll_all()
                self._cached = data
                return data
        except (ModbusError, asyncio.TimeoutError, OSError) as exc:
            if self._cached:
                _LOGGER.debug(
                    "Poll failed (%s), keeping last known values until next cycle",
                    exc,
                )
                return self._cached
            raise UpdateFailed(f"Poll failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    async def _write(self, address: int, value: int) -> None:
        """Write a single register. Uses its own TCP session."""
        try:
            async with self._bus_lock:
                async with self._client:
                    await self._client.write_register(address, value)
        except (ModbusError, asyncio.TimeoutError, OSError) as exc:
            _LOGGER.warning("Write to register %d failed: %s", address, exc)
            raise

    def _notify(self, updates: dict) -> None:
        """Apply optimistic updates to cache and push to all listeners immediately."""
        self._cached.update(updates)
        self.async_set_updated_data(self._cached)

    async def async_turn_on(self) -> None:
        ctrl = self._cached.get("control_word", 0)
        new_ctrl = ctrl | CTRL_ON_OFF
        await self._write(REG_CONTROL_WORD, new_ctrl)
        self._notify({
            "control_word": new_ctrl,
            "unit_on": True,
            "mode_id": new_ctrl & CTRL_MODE_MASK,
        })

    async def async_turn_off(self) -> None:
        ctrl = self._cached.get("control_word", 0)
        new_ctrl = ctrl & ~CTRL_ON_OFF & 0xFFFF
        await self._write(REG_CONTROL_WORD, new_ctrl)
        self._notify({
            "control_word": new_ctrl,
            "unit_on": False,
            "mode_id": new_ctrl & CTRL_MODE_MASK,
        })

    async def async_set_mode(self, mode_id: int) -> None:
        ctrl = self._cached.get("control_word", 0)
        new_ctrl = (ctrl & ~CTRL_MODE_MASK) | (mode_id & CTRL_MODE_MASK)
        await self._write(REG_CONTROL_WORD, new_ctrl)
        self._notify({
            "control_word": new_ctrl,
            "unit_on": bool(new_ctrl & CTRL_ON_OFF),
            "mode_id": new_ctrl & CTRL_MODE_MASK,
        })

    async def async_set_target_temp(self, temp_c: float) -> None:
        clamped = round(max(25.0, min(60.0, temp_c)), 1)
        raw = int(clamped * 10)
        await self._write(REG_SET_TEMP, raw)
        self._notify({
            "set_temp_raw": raw,
            "set_temp": clamped,
        })