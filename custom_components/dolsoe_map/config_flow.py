import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN, 
    CONF_MOWER_WIDTH, 
    DEFAULT_MOWER_WIDTH
)

class DolsoeMapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """설정 흐름 관리 (UI 입력창)."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """처음 통합구성요소를 추가할 때 실행되는 단계."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"돌쇠 맵 ({user_input['source_entity']})", 
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("source_entity", default="device_tracker.dolsoe_405x"): str,
                vol.Required("map_path", default="/config/www/maps/mower_map.png"): str,
                vol.Required("mower_path", default="/config/www/maps/mower_icon.png"): str,
                vol.Required("top_left", default="35.4755234, 129.2316285"): str,
                vol.Required("bottom_right", default="35.4751542, 129.2317375"): str,
                vol.Required("rotation", default=19): int,
                vol.Optional(CONF_MOWER_WIDTH, default=DEFAULT_MOWER_WIDTH): int,
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """옵션 흐름(구성 버튼)을 연결합니다."""
        return DolsoeMapOptionsFlow(config_entry)


class DolsoeMapOptionsFlow(config_entries.OptionsFlow):
    """설치 후 '구성' 버튼을 눌렀을 때 실행되는 로직."""
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """옵션 설정 화면."""
        if user_input is not None:
            # 기존 데이터를 유지하면서 변경된 옵션값(mower_width 등)만 업데이트
            new_data = dict(self.config_entry.data)
            new_data.update(user_input)
            self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                # 기존에 저장된 값을 default로 보여줍니다.
                vol.Optional(
                    CONF_MOWER_WIDTH, 
                    default=self.config_entry.data.get(CONF_MOWER_WIDTH, DEFAULT_MOWER_WIDTH)
                ): int,
                # 다른 설정값(회전 등)도 수정하고 싶다면 여기에 추가 가능합니다.
                vol.Optional(
                    "rotation", 
                    default=self.config_entry.data.get("rotation", 19)
                ): int,
            })
        )
