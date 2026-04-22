from __future__ import annotations
from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DuroosyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DuroosyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        DuroosyNextLessonSensor(coordinator, "title", "Next Lesson Title", None),
        DuroosyNextLessonSensor(coordinator, "start_time", "Next Lesson Start", SensorDeviceClass.TIMESTAMP),
        DuroosyNextLessonSensor(coordinator, "student_names", "Next Lesson Students", None),
        DuroosyNextLessonSensor(coordinator, "minutes_until_start", "Next Lesson Minutes Until Start", None),
        DuroosyScheduleSensor(coordinator),
    ])


class DuroosyNextLessonSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: DuroosyCoordinator, field: str, name: str, device_class) -> None:
        super().__init__(coordinator)
        self._field = field
        self._attr_name = f"Duroosy {name}"
        self._attr_unique_id = f"duroosy_next_lesson_{field}"
        self._attr_device_class = device_class

    @property
    def native_value(self):
        lessons = (self.coordinator.data or {}).get("lessons", [])
        if not lessons:
            return None
        val = lessons[0].get(self._field)
        if self._field == "start_time" and val:
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except ValueError:
                return val
        if self._field == "student_names" and isinstance(val, list):
            return ", ".join(val)
        return val

    @property
    def extra_state_attributes(self):
        lessons = (self.coordinator.data or {}).get("lessons", [])
        if not lessons:
            return {}
        return {k: v for k, v in lessons[0].items() if k != self._field}


class DuroosyScheduleSensor(CoordinatorEntity, SensorEntity):
    """Exposes the full lesson schedule for today as a sensor with attributes."""

    def __init__(self, coordinator: DuroosyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Duroosy Today Schedule"
        self._attr_unique_id = "duroosy_today_schedule"

    @property
    def native_value(self) -> int:
        lessons = (self.coordinator.data or {}).get("lessons", [])
        today = datetime.utcnow().date().isoformat()
        return sum(1 for l in lessons if l.get("start_time", "").startswith(today))

    @property
    def extra_state_attributes(self):
        lessons = (self.coordinator.data or {}).get("lessons", [])
        today = datetime.utcnow().date().isoformat()
        today_lessons = [l for l in lessons if l.get("start_time", "").startswith(today)]
        return {
            "lessons": today_lessons,
            "updated_at": (self.coordinator.data or {}).get("updated_at"),
        }
