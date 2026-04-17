"""Config flow for Polytropic Heat Pump."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SLAVE
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .modbus_client import ModbusRTUClient, ModbusError
from .const import CONF_DEBUG, REG_CONTROL_WORD

_LOGGER = logging.getLogger(__name__)

DOMAIN = "polytropic_heatpump"

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Required(CONF_PORT, default=8899): NumberSelector(
            NumberSelectorConfig(min=1, max=65535, step=1, mode=NumberSelectorMode.BOX)
        ),
        vol.Required(CONF_SLAVE, default=17): NumberSelector(
            NumberSelectorConfig(min=1, max=247, step=1, mode=NumberSelectorMode.BOX)
        ),
    }
)


class PolytropicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Polytropic Heat Pump."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "PolytropicOptionsFlow":
        return PolytropicOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host  = user_input[CONF_HOST]
            port  = int(user_input[CONF_PORT])
            slave = int(user_input[CONF_SLAVE])

            await self.async_set_unique_id(f"{host}:{port}:{slave}")
            self._abort_if_unique_id_configured()

            client = ModbusRTUClient(host=host, port=port, slave=slave, timeout=5.0)
            try:
                async with asyncio.timeout(6.0):
                    async with client:
                        await client.read_holding_register(REG_CONTROL_WORD)
            except ModbusError as exc:
                _LOGGER.debug("Modbus probe failed: %s", exc)
                errors["base"] = "modbus_error"
            except (TimeoutError, asyncio.TimeoutError, OSError, ConnectionRefusedError) as exc:
                _LOGGER.debug("Cannot connect: %s", exc)
                errors["base"] = "cannot_connect"
            except Exception as exc:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during probe: %s", exc)
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=f"Polytropic Heat Pump ({host})",
                    data={CONF_HOST: host, CONF_PORT: port, CONF_SLAVE: slave},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )


class PolytropicOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Polytropic Heat Pump."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEBUG,
                        default=self.config_entry.options.get(CONF_DEBUG, False),
                    ): BooleanSelector(),
                }
            ),
        )
