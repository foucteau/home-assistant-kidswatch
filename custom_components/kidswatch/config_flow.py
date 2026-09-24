from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KidsWatchAuthenticationError, KidsWatchClient, KidsWatchError
from .const import CONF_COUNTRY_CODE, CONF_M2, CONF_PHONE, DEFAULT_COUNTRY_CODE, DOMAIN
from .machine_id import generate_machine_m2

_LOGGER = logging.getLogger(__name__)


class KidsWatchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the KidsWatch config flow."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            phone = user_input[CONF_PHONE].strip()
            password = user_input[CONF_PASSWORD]
            country_code = user_input[CONF_COUNTRY_CODE].strip()

            if not country_code or not phone or not password:
                errors["base"] = "missing_fields"
            else:
                m2 = generate_machine_m2(self.hass)
                client = KidsWatchClient(
                    session=async_get_clientsession(self.hass),
                    phone=phone,
                    password=password,
                    country_code=country_code,
                    m2=m2,
                )
                try:
                    await client.login()
                except KidsWatchAuthenticationError:
                    errors["base"] = "invalid_auth"
                except KidsWatchError:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected KidsWatch setup error")
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(client.qid or phone)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="KidsWatch",
                        data={
                            CONF_PHONE: phone,
                            CONF_PASSWORD: password,
                            CONF_COUNTRY_CODE: country_code,
                            CONF_M2: m2,
                        },
                    )

        country_default = (user_input or {}).get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE)
        phone_default = (user_input or {}).get(CONF_PHONE, "")
        password_default = (user_input or {}).get(CONF_PASSWORD, "")
        schema = vol.Schema({
            vol.Required(CONF_COUNTRY_CODE, default=country_default): str,
            vol.Required(CONF_PHONE, default=phone_default): str,
            vol.Required(CONF_PASSWORD, default=password_default): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
