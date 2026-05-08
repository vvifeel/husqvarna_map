import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class DolsoeMapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """설정 흐름 관리 (UI 입력창)."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=f"돌쇠 맵 ({user_input['source_entity']})", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                # 데이터를 가져올 엔티티 ID를 입력받습니다.
                vol.Required("source_entity", default="device_tracker.dolsoe_405x"): str,
                vol.Required("map_path", default="/config/www/maps/mower_map.png"): str,
                vol.Required("mower_path", default="/config/www/maps/mower_icon.png"): str,
                vol.Required("top_left", default="35.4755234, 129.2316285"): str,
                vol.Required("bottom_right", default="35.4751542, 129.2317375"): str,
                vol.Required("rotation", default=19): int,
            })
        )
