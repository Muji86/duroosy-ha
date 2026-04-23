from __future__ import annotations
from datetime import datetime, timezone
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
        DuroosyNextLessonTitleSensor(coordinator),
        DuroosyNextLessonStartSensor(coordinator),
        DuroosyNextLessonStudentsSensor(coordinator),
        DuroosyNextLessonMinutesSensor(coordinator),
        DuroosyScheduleSensor(coordinator),
    ])


def _next_lesson(coordinator: DuroosyCoordinator) -> dict | None:
    lessons = (coordinator.data or {}).get("lessons", [])
    now = datetime.now(timezone.utc)
    upcoming = [
        l for l in lessons
        if datetime.fromisoformat(l["start_time"]).astimezone(timezone.utc) > now
        and l.get("start_time")
    ]
    return upcoming[0] if upcoming else None


class _DuroosyBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: DuroosyCoordinator, unique_suffix: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"duroosy_{unique_suffix}"

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None


class DuroosyNextLessonTitleSensor(_DuroosyBaseSensor):
    _attr_name = "Duroosy Next Lesson Title"
    _attr_icon = "mdi:school"

    def __init__(self, coordinator: DuroosyCoordinator) -> None:
        super().__init__(coordinator, "next_lesson_title")

    @property
    def native_value(self) -> str | None:
        lesson = _next_lesson(self.coordinator)
        return lesson.get("lesson_title") if lesson else None

    @property
    def extra_state_attributes(self) -> dict:
        lesson = _next_lesson(self.coordinator)
        if not lesson:
            return {}
        return {
            "student_names": lesson.get("student_names", []),
            "student_names_ar": lesson.get("student_names_ar", []),
            "duration_minutes": lesson.get("duration_minutes"),
            "start_time": lesson.get("start_time"),
        }


class DuroosyNextLessonStartSensor(_DuroosyBaseSensor):
    _attr_name = "Duroosy Next Lesson Start"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:calendar-clock"
    _attr_force_update = True

    def __init__(self, coordinator: DuroosyCoordinator) -> None:
        super().__init__(coordinator, "next_lesson_start")

    @property
    def native_value(self) -> datetime | None:
        lesson = _next_lesson(self.coordinator)
        if not lesson:
            return None
        val = lesson.get("start_time")
        if not val:
            return None
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None


class DuroosyNextLessonStudentsSensor(_DuroosyBaseSensor):
    _attr_name = "Duroosy Next Lesson Students"
    _attr_icon = "mdi:account-group"

    def __init__(self, coordinator: DuroosyCoordinator) -> None:
        super().__init__(coordinator, "next_lesson_students")

    @property
    def native_value(self) -> str | None:
        lesson = _next_lesson(self.coordinator)
        if not lesson:
            return None
        names = lesson.get("student_names", [])
        return ", ".join(names) if names else None


class DuroosyNextLessonMinutesSensor(_DuroosyBaseSensor):
    _attr_name = "Duroosy Next Lesson Minutes Until Start"
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator: DuroosyCoordinator) -> None:
        super().__init__(coordinator, "next_lesson_minutes_until_start")

    @property
    def native_value(self) -> int | None:
        lesson = _next_lesson(self.coordinator)
        if not lesson:
            return None
        val = lesson.get("start_time")
        if not val:
            return None
        try:
            start = datetime.fromisoformat(val.replace("Z", "+00:00"))
            diff = (start - datetime.now(timezone.utc)).total_seconds() / 60
            return max(0, round(diff))
        except ValueError:
            return None


class DuroosyScheduleSensor(_DuroosyBaseSensor):
    _attr_name = "Duroosy Today Schedule"
    _attr_icon = "mdi:calendar-today"

    def __init__(self, coordinator: DuroosyCoordinator) -> None:
        super().__init__(coordinator, "today_schedule")

    @property
    def native_value(self) -> int:
        lessons = (self.coordinator.data or {}).get("lessons", [])
        today = datetime.now(timezone.utc).date().isoformat()
        return sum(1 for l in lessons if l.get("start_time", "").startswith(today))

    @property
    def extra_state_attributes(self) -> dict:
        lessons = (self.coordinator.data or {}).get("lessons", [])
        today = datetime.now(timezone.utc).date().isoformat()
        today_lessons = [l for l in lessons if l.get("start_time", "").startswith(today)]
        return {
            "lessons": today_lessons,
            "updated_at": (self.coordinator.data or {}).get("updated_at"),
        }
