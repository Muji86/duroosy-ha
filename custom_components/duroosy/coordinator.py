from datetime import timedelta
import logging
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class DuroosyCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        self.api_key = api_key
        super().__init__(
            hass,
            _LOGGER,
            name="Duroosy",
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )

    async def _async_update_data(self) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    API_URL,
                    headers={"x-duroosy-api-key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 401:
                        raise UpdateFailed("Invalid Duroosy API key")
                    resp.raise_for_status()
                    return await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Duroosy API: {err}") from err
