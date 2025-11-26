"""Config flow for MOOX Track integration.

Copyright 2025 MOOX SRLS
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from aiohttp import CookieJar

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import (
    CONF_CUSTOM_ATTRIBUTES,
    CONF_EMAIL,
    CONF_EVENTS,
    CONF_MAX_ACCURACY,
    CONF_SKIP_ACCURACY_FILTER_FOR,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    EVENTS,
    LOGGER,
)
from .moox_client import (
    MooxAuthenticationException,
    MooxClient,
    MooxException,
    ServerModel,
)

try:
    from homeassistant.helpers import selector as selectors
except ImportError:
    selectors = None  # type: ignore[assignment]

SELECTORS_SUPPORTED = bool(
    selectors is not None
    and hasattr(selectors, "TextSelector")
    and hasattr(selectors, "TextSelectorConfig")
    and hasattr(selectors, "TextSelectorType")
    and hasattr(selectors, "NumberSelector")
    and hasattr(selectors, "NumberSelectorConfig")
    and hasattr(selectors, "NumberSelectorMode")
    and hasattr(selectors, "SelectSelector")
    and hasattr(selectors, "SelectSelectorConfig")
    and hasattr(selectors, "SelectSelectorMode")
)

if SELECTORS_SUPPORTED:
    STEP_USER_DATA_SCHEMA = vol.Schema(
        {
            vol.Required(CONF_EMAIL): selectors.TextSelector(
                selectors.TextSelectorConfig(type=selectors.TextSelectorType.EMAIL)
            ),
            vol.Required(CONF_PASSWORD): selectors.TextSelector(
                selectors.TextSelectorConfig(type=selectors.TextSelectorType.PASSWORD)
            ),
        }
    )
else:
    STEP_USER_DATA_SCHEMA = vol.Schema(
        {
            vol.Required(CONF_EMAIL): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
        }
    )


def _get_options_schema() -> vol.Schema:
    """Get options schema."""
    if SELECTORS_SUPPORTED:
        return vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=30
                ): selectors.NumberSelector(
                    selectors.NumberSelectorConfig(
                        mode=selectors.NumberSelectorMode.BOX,
                        min=30,
                        step=1,
                        unit_of_measurement="s",
                    )
                ),
                vol.Optional(
                    CONF_MAX_ACCURACY, default=0.0
                ): selectors.NumberSelector(
                    selectors.NumberSelectorConfig(
                        mode=selectors.NumberSelectorMode.BOX,
                        min=0.0,
                    )
                ),
                vol.Optional(
                    CONF_CUSTOM_ATTRIBUTES, default=[]
                ): selectors.SelectSelector(
                    selectors.SelectSelectorConfig(
                        mode=selectors.SelectSelectorMode.DROPDOWN,
                        multiple=True,
                        sort=True,
                        custom_value=True,
                        options=[],
                    )
                ),
                vol.Optional(
                    CONF_SKIP_ACCURACY_FILTER_FOR, default=[]
                ): selectors.SelectSelector(
                    selectors.SelectSelectorConfig(
                        mode=selectors.SelectSelectorMode.DROPDOWN,
                        multiple=True,
                        sort=True,
                        custom_value=True,
                        options=[],
                    )
                ),
                vol.Optional(CONF_EVENTS, default=[]): selectors.SelectSelector(
                    selectors.SelectSelectorConfig(
                        mode=selectors.SelectSelectorMode.DROPDOWN,
                        multiple=True,
                        sort=True,
                        custom_value=True,
                        options=list(EVENTS),
                    )
                ),
            }
        )

    return vol.Schema(
        {
            vol.Optional(CONF_UPDATE_INTERVAL, default=30): vol.All(
                vol.Coerce(int),
                vol.Range(min=30),
            ),
            vol.Optional(CONF_MAX_ACCURACY, default=0.0): vol.All(
                vol.Coerce(float),
                vol.Range(min=0.0),
            ),
            vol.Optional(CONF_CUSTOM_ATTRIBUTES, default=[]): cv.ensure_list(
                cv.string
            ),
            vol.Optional(CONF_SKIP_ACCURACY_FILTER_FOR, default=[]): cv.ensure_list(
                cv.string
            ),
            vol.Optional(CONF_EVENTS, default=[]): cv.ensure_list(cv.string),
        }
    )


class MooxOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for the MOOX Track integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow handler."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_get_options_schema(),
        )


class MooxServerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MOOX Track."""

    VERSION = 2

    async def _get_server_info(self, user_input: dict[str, Any]) -> ServerModel:
        """Validate credentials by fetching server info."""
        ssl = user_input.get(CONF_SSL, True)
        verify_ssl = user_input.get(CONF_VERIFY_SSL, True)
        client_session = async_create_clientsession(
            self.hass,
            cookie_jar=CookieJar(unsafe=not ssl or not verify_ssl),
        )
        client = MooxClient(
            client_session=client_session,
            host=user_input[CONF_HOST],
            port=user_input[CONF_PORT],
            ssl=ssl,
            verify_ssl=verify_ssl,
            username=user_input[CONF_EMAIL],
            password=user_input[CONF_PASSWORD],
        )
        return await client.get_server()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {
                **user_input,
                CONF_HOST: "app.moox.it",
                CONF_PORT: 443,
                CONF_SSL: True,
                CONF_VERIFY_SSL: True,
            }

            try:
                await self._get_server_info(data)
            except MooxAuthenticationException:
                LOGGER.error("Invalid credentials for MOOX Track")
                errors["base"] = "invalid_auth"
            except MooxException as exception:
                LOGGER.error("Unable to connect to MOOX Track: %s", exception)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{data[CONF_HOST]}:{data[CONF_PORT]}",
                    data=data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle re-authentication confirmation."""
        reauth_entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            test_data = dict(reauth_entry.data)
            test_data[CONF_EMAIL] = user_input[CONF_EMAIL]
            test_data[CONF_PASSWORD] = user_input[CONF_PASSWORD]
            try:
                await self._get_server_info(test_data)
            except MooxAuthenticationException:
                LOGGER.error("Invalid credentials for MOOX Track")
                errors["base"] = "invalid_auth"
            except MooxException as exception:
                LOGGER.error("Unable to connect to MOOX Track: %s", exception)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                CONF_HOST: reauth_entry.data.get(CONF_HOST, "app.moox.it"),
                CONF_PORT: str(reauth_entry.data.get(CONF_PORT, 443)),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return MooxOptionsFlowHandler(config_entry)
