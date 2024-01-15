"""Platform for sensor integration."""
from __future__ import annotations

import asyncio.timeouts
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
import json
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfLength,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import MyFiskerAPI
from .const import DOMAIN, CLIMATE_CONTROL_SEAT_HEAT

_LOGGER = logging.getLogger(__name__)


@dataclass
class FiskerEntityDescription(SensorEntityDescription):
    """Describes MyFisker ID sensor entity."""

    def __init__(self, key, name, icon, native_unit_of_measurement, value):
        self.key = key
        self.name = name
        self.icon = icon
        self.native_unit_of_measurement = native_unit_of_measurement
        self.value = value

    # value: Callable = lambda x, y: x

    def get_value(self, data):
        return self.value(data, self.key)


SENSORS: tuple[SensorEntityDescription, ...] = (
    FiskerEntityDescription(
        key="battery_avg_cell_temp",
        name="Battery avg. cell temp",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_charge_type",
        name="Battery charge type",
        icon="mdi:car",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_max_miles",
        name="Battery max miles",
        icon="mdi:car",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_percent",
        name="Battery percent",
        icon="mdi:battery-70",
        native_unit_of_measurement=PERCENTAGE,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_state_of_charge",
        name="Battery state of charge",
        icon="mdi:car-electric",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_total_mileage_odometer",
        name="Total mileage odometer",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_ambient_temperature",
        name="Ambient temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_cabin_temperature",
        name="Cabin temperature",
        icon="mdi:temperature-celsius",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_driver_seat_heat",
        name="Driver seat heating",
        icon="mdi:car-seat-heater",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_internal_temperature",
        name="Internal temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_passenger_seat_heat",
        name="Passenger seat heating",
        icon="mdi:car-seat-heater",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_rear_defrost",
        name="Rear window defrost",
        icon="mdi:car-defrost-rear",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_steering_wheel_heat",
        name="Steering wheel heat",
        icon="mdi:steering",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="door_locks_all",
        name="Door locks all",
        icon="mdi:car-door-lock",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="door_locks_driver",
        name="Door locks driver",
        icon="mdi:car-door-lock",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_hood",
        name="Doors hood",
        icon="mdi:car-door-lock",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_left_front",
        name="Doors left front",
        icon="mdi:car-door-lock",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_left_rear",
        name="Doors left rear",
        icon="mdi:car-door-lock",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_right_front",
        name="Doors right front",
        icon="mdi:car-door-lock",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_right_rear",
        name="Doors right rear",
        icon="mdi:car-door-lock",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="doors_trunk",
        name="Doors trunk",
        icon="mdi:car-door-lock",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="gear_in_park",
        name="Gear in park",
        icon="mdi:car-brake-parking",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="ip",
        name="IP address",
        icon="mdi:ip",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="location_altitude",
        name="Location altitude",
        icon="mdi:altimeter",
        native_unit_of_measurement=UnitOfLength.METERS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="location_latitude",
        name="Location latitude",
        icon="mdi:map-marker-radius",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="location_longitude",
        name="Location longitude",
        icon="mdi:map-marker-radius",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="online",
        name="online State",
        icon="mdi:car-connected",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="online_hmi",
        name="Online hmi",
        icon="mdi:car-connected",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="trex_version",
        name="trex version",
        icon="mdi:car-info",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="updated",
        name="Last updated",
        icon="mdi:car-info",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="vehicle_speed_speed",
        name="Vehicle speed",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="vin",
        name="Vehicle identification no",
        icon="mdi:car-info",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_left_front",
        name="windows_left_front",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_left_rear",
        name="windows_left_rear",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_left_rear_quarter",
        name="windows_left_rear_quarter",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_rear_windshield",
        name="windows_rear_windshield",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_right_front",
        name="windows_right_front",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_right_rear",
        name="windows_right_rear",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_right_rear_quarter",
        name="windows_right_rear_quarter",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_sunroof",
        name="windows_sunroof",
        icon="mdi:car-select",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
)


# Get an item by its key
def get_sensor_by_key(key):
    for sensor in SENSORS:
        if sensor.key == key:
            return sensor


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.debug("Setup sensors")

    my_Fisker = hass.data[DOMAIN][entry.entry_id]

    data = entry.data
    myFiskerApi = MyFiskerAPI(data[CONF_USERNAME], data[CONF_PASSWORD])
    token = await myFiskerApi.GetAuthTokenAsync()

    # Fetch initial data so we have data when entities subscribe
    coordinator = MyCoordinator(hass, myFiskerApi)

    await coordinator.async_config_entry_first_refresh()

    entities: list[FiskerSensor] = []

    # for sensor in SENSORS:
    for idx in enumerate(coordinator.data):
        sens = get_sensor_by_key(idx[1])
        entities.append(FiskerSensor(coordinator, idx, sens, my_Fisker))

    # async_add_entities(
    #     FiskerSensorNy(coordinator, idx, SENSORS[idx], my_Fisker)
    #     for idx, ent in enumerate(coordinator.data)
    # )

    # Add entities to Home Assistant
    async_add_entities(entities)


class MyCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, my_api: MyFiskerAPI):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="MyFisker sensor",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self.my_fisker_api = my_api

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """

        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already handled by the data update coordinator.
            async with asyncio.timeout(30):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit data retrieved from API.
                # listening_idx = set(self.async_contexts())

                token = await self.my_fisker_api.GetAuthTokenAsync()
                retData = await self.my_fisker_api.fetch_data()
                return retData
        except:
            _LOGGER.error("MyCoordinator _async_update_data failed")
        # except ApiAuthError as err:
        #     # Raising ConfigEntryAuthFailed will cancel future updates
        #     # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #     raise ConfigEntryAuthFailed from err
        # except ApiError as err:
        #     raise UpdateFailed(f"Error communicating with API: {err}")


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    # Code for setting up your platform inside of the event loop
    _LOGGER.debug("async_setup_platform")


class FiskerSensor(CoordinatorEntity, SensorEntity):
    # An entity using CoordinatorEntity.

    def __init__(self, coordinator, idx, sensor: FiskerEntityDescription, client):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        self._sensor = sensor
        self._data = client
        self._coordinator = coordinator
        self._attr_name = sensor.name
        self._attr_unique_id = f"{self._coordinator.data['vin']}_{sensor.key}"
        self.icon = self._sensor.icon

        if sensor.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self):
        """Return device information about this entity."""
        _LOGGER.debug("My Fisker: device_info")

        return {
            "identifiers": {
                # Unique identifiers within a specific domain
                (DOMAIN, self._coordinator.data["vin"])
            },
            "manufacturer": "Fisker inc.",
            "model": "Fisker (Ocean)",
            "name": self._data.get_name(),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # self._attr_is_on = 12334  # self.coordinator.data[self.idx]["state"]

        if "seat_heat" in self._sensor.key:
            self.mode = CLIMATE_CONTROL_SEAT_HEAT.get(
                self.state, CLIMATE_CONTROL_SEAT_HEAT[0]
            )
            self._attr_native_value = self.mode[0]

        self._attr_available = True

        self._attr_is_on = True

        self.async_write_ha_state()

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def should_poll(self):
        return False

    @property
    def state(self):
        try:
            state = self._sensor.get_value(self.coordinator.data)

        except (KeyError, ValueError):
            return None
        return state

    # async def async_turn_on(self, **kwargs):
    #     """Turn the light on.

    #     Example method how to request data updates.
    #     """
    #     # Do the turning on.
    #     # ...

    #     # Update the data
    #     await self.coordinator.async_request_refresh()