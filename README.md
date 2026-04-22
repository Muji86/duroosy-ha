# Duroosy Home Assistant Integration

Adds your Duroosy lesson schedule as sensors in Home Assistant, so you can build automations like "announce 15 minutes before a lesson starts."

## Installation

1. In HACS → Custom Repositories, add `Muji86/duroosy-ha` as an **Integration**
2. Search for "Duroosy" and install
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration** → search "Duroosy"
5. Paste your API key from the Duroosy app (**Profile → Home Assistant → Generate API Key**)

## Sensors

| Entity | Description |
|--------|-------------|
| `sensor.duroosy_next_lesson_title` | Title of the next upcoming lesson |
| `sensor.duroosy_next_lesson_start` | Start time (timestamp) of the next lesson |
| `sensor.duroosy_next_lesson_students` | Student name(s) for the next lesson |
| `sensor.duroosy_next_lesson_minutes_until_start` | Minutes until next lesson starts |
| `sensor.duroosy_today_schedule` | Number of lessons today; full schedule in attributes |

## Example Automation

Announce 15 minutes before a lesson:

```yaml
automation:
  - alias: "Lesson starting soon"
    trigger:
      - platform: numeric_state
        entity_id: sensor.duroosy_next_lesson_minutes_until_start
        below: 16
        above: 14
    action:
      - service: tts.speak
        target:
          entity_id: tts.home_assistant_cloud
        data:
          message: >
            {{ state_attr('sensor.duroosy_next_lesson_minutes_until_start', 'student_names') }}'s
            {{ states('sensor.duroosy_next_lesson_title') }} lesson starts in 15 minutes.
          media_player_entity_id: media_player.living_room_speaker
```
