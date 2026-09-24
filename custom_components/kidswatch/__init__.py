from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import API_VERSION, KidsWatchClient
from .const import CONF_COUNTRY_CODE, CONF_M2, CONF_PHONE, DOMAIN
from .coordinator import KidsWatchCoordinator
from .machine_id import generate_machine_m2

_LOGGER = logging.getLogger(__name__)
INIT_VERSION = "0.1.8"
PLATFORMS = [Platform.SENSOR, Platform.DEVICE_TRACKER, Platform.BUTTON]


def _language(hass: HomeAssistant) -> str:
    return str(getattr(hass.config, "language", None) or "en").replace("-", "_")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up KidsWatch from a config entry."""
    _LOGGER.info("KidsWatch integration %s loaded (API %s)", INIT_VERSION, API_VERSION)

    machine_m2 = generate_machine_m2(hass)
    if entry.data.get(CONF_M2) != machine_m2:
        new_data = dict(entry.data)
        new_data[CONF_M2] = machine_m2
        hass.config_entries.async_update_entry(entry, data=new_data)

    client = KidsWatchClient(
        session=async_get_clientsession(hass),
        phone=entry.data[CONF_PHONE],
        password=entry.data[CONF_PASSWORD],
        country_code=entry.data[CONF_COUNTRY_CODE],
        m2=machine_m2,
        time_zone=str(hass.config.time_zone),
        user_lang=_language(hass),
    )
    await client.login()

    coordinator = KidsWatchCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"client": client, "coordinator": coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a KidsWatch config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
