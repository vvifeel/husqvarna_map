from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """설정 항목으로부터 컴포넌트 셋업."""
    await hass.config_entries.async_forward_entry_setups(entry, ["image"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """설정 항목 제거."""
    return await hass.config_entries.async_unload_platforms(entry, ["image"])
