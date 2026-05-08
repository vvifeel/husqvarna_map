import io
import math
import logging
from datetime import datetime
from PIL import Image, ImageDraw
from geopy.distance import distance, geodesic

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([DolsoeHybridImage(hass, entry)])

class DolsoeHybridImage(ImageEntity):
    def __init__(self, hass, entry):
        super().__init__(hass)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_image"
        self._attr_name = "Dolsoe Hybrid Map"
        
        # UI에서 입력받은 설정값
        self._map_path = entry.data["map_path"]
        self._mower_path = entry.data["mower_path"]
        self._top_left = tuple(map(float, entry.data["top_left"].split(",")))
        self._bottom_right = tuple(map(float, entry.data["bottom_right"].split(",")))
        self._rotation = entry.data["rotation"]
        
        # 경로 저장용 메모리 변수
        self._pos_history = []
        self._load_images()
        
        # [기존 코드 로직 유지] 스케일 및 중심점 계산
        self._px_meter = self._calculate_px_meter()
        self._center_wgs84 = ((self._top_left[0] + self._bottom_right[0]) / 2, (self._top_left[1] + self._bottom_right[1]) / 2)
        self._center_px = (self._base_map.size[0] // 2, self._base_map.size[1] // 2)

    def _load_images(self):
        """이미지 파일 로드 및 최적화."""
        self._base_map = Image.open(self._map_path).convert("RGBA")
        self._mower_icon = Image.open(self._mower_path).convert("RGBA")
        if self._mower_icon.size[0] > 64:
            self._mower_icon.thumbnail((64, 64), Image.Resampling.LANCZOS)
        self._image = self._base_map.copy()

    def _calculate_px_meter(self):
        """[기존 로직 유지] m당 픽셀 비 계산."""
        dist_m = geodesic(self._top_left, self._bottom_right).meters
        dist_px = math.dist((0, 0), self._base_map.size)
        return dist_px / dist_m

    async def async_image(self) -> bytes | None:
        """[핵심 수정] 공식 엔티티 데이터를 읽어와서 이미지를 생성."""
        # 공식 컴포넌트의 엔티티 ID를 직접 참조합니다.
        state = self.hass.states.get("device_tracker.dolsoe_405x")
        
        if state and "latitude" in state.attributes:
            lat, lon = state.attributes["latitude"], state.attributes["longitude"]
            new_p = (lat, lon)
            
            # 좌표가 새롭게 업데이트된 경우에만 렌더링 수행
            if not self._pos_history or self._pos_history[0] != new_p:
                self._pos_history.insert(0, new_p)
                if len(self._pos_history) > 1000: self._pos_history.pop() # 메모리 관리
                self._draw()
        
        img_byte_arr = io.BytesIO()
        self._image.save(img_byte_arr, format="PNG")
        return img_byte_arr.getvalue()

    def _draw(self):
        """[기존 로직 유지] 경로와 마커를 그리는 함수."""
        new_img = self._base_map.copy()
        draw = ImageDraw.Draw(new_img)
        
        # 1. 경로 그리기
        if len(self._pos_history) > 1:
            for i in range(len(self._pos_history) - 1):
                p1 = self._scale_to_img(self._pos_history[i])
                p2 = self._scale_to_img(self._pos_history[i+1])
                # 기존에 사용하던 색상 유지 (반투명 노란색 계열)
                draw.line([p1, p2], fill=(228, 224, 152, 200), width=4)

        # 2. 현재 위치 마커 배치
        if self._pos_history:
            curr_px = self._scale_to_img(self._pos_history[0])
            m_w, m_h = self._mower_icon.size
            new_img.paste(self._mower_icon, (curr_px[0] - m_w // 2, curr_px[1] - m_h // 2), self._mower_icon)

        self._image = new_img
        self._attr_image_last_updated = datetime.now()

    def _scale_to_img(self, lat_lon):
        """[기존 로직 유지] GPS 좌표를 픽셀 좌표로 변환."""
        res = distance(self._center_wgs84, lat_lon).geod.Inverse(self._center_wgs84[0], self._center_wgs84[1], lat_lon[0], lat_lon[1])
        c_bearing = math.radians(res.get("azi1") - 90 + self._rotation)
        c_dist_m = res.get("s12") * 1000
        
        new_x = self._center_px[0] + (c_dist_m * self._px_meter * math.cos(c_bearing))
        new_y = self._center_px[1] + (c_dist_m * self._px_meter * math.sin(c_bearing))
        return int(new_x), int(new_y)
