"""Platform for sensor integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
import json
import logging
from typing import cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CLIMATE_CONTROL_SEAT_HEAT, DOMAIN, LIST_CLIMATE_CONTROL_SEAT_HEAT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.debug("Setup sensors")

    my_Fisker_data = hass.data[DOMAIN][entry.entry_id]

    coordinator = my_Fisker_data._coordinator

    entities: list[FiskerSensor] = []

    # for sensor in SENSORS:
    for idx in enumerate(coordinator.data):
        sens = get_sensor_by_key(idx[1])
        if sens is None:
            _LOGGER.warning(idx[1])
        else:
            entities.append(FiskerSensor(coordinator, idx, sens, my_Fisker_data))

    # Add entities to Home Assistant
    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    # Code for setting up your platform inside of the event loop
    _LOGGER.debug("async_setup_platform")


class FiskerSensor(CoordinatorEntity, SensorEntity):
    # An entity using CoordinatorEntity.

    def __init__(self, coordinator, idx, sensor: FiskerEntityDescription, client):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        # self._sensor = sensor
        self._data = client
        self._coordinator = coordinator
        self.entity_description = sensor
        self._attr_unique_id = f"{self._coordinator.data['vin']}_{sensor.key}"
        self._attr_name = f"{self._coordinator._alias} {sensor.name}"

        _LOGGER.info(self._attr_unique_id)
        # self.icon = self._sensor.icon

        if sensor.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            if "seat_heat" in self.entity_description.key:
                self.options = LIST_CLIMATE_CONTROL_SEAT_HEAT
                self.device_class = SensorDeviceClass.ENUM

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
            "name": self._coordinator._alias,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        value = self._coordinator.data[self.idx[1]]
        data_available = True

        if "seat_heat" in self.entity_description.key:
            self._attr_native_value = CLIMATE_CONTROL_SEAT_HEAT[value][0]
        elif "battery_max_miles" in self.entity_description.key:
            batt = self._coordinator.data["battery_percent"]
            _LOGGER.debug(f"battery_data: max_miles={value}, percent:{batt}")
            if (
                value <= 3 and batt >= 3
            ):  # work around to avoid vehicle sometimes reporting '0 km' remaining
                self._attr_native_value = None
                data_available = False
            else:
                self._attr_native_value = value
        else:
            self._attr_native_value = value

        self._attr_available = data_available

        self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def friendly_name(self):
        return self.entity_description.name

    @property
    def state(self):
        try:
            state = self._attr_native_value
        except (KeyError, ValueError):
            return None
        return state


# Get an item by its key
def get_sensor_by_key(key):
    for sensor in SENSORS:
        if sensor.key == key:
            return sensor


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
        key="battery_remaining_charging_time",
        name="Battery remaining charging time",
        icon="mdi:battery-clock-outline",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_remaining_charging_time_full",
        name="Battery remaining charging time full",
        icon="mdi:battery-clock-outline",
        native_unit_of_measurement=UnitOfTime.MINUTES,
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
        name="Battery total mileage odometer",
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
        key="trex_version",
        name="Trex version",
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
        name="VIN no",
        icon="mdi:car-info",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_left_front",
        name="Window front left",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_left_rear",
        name="window rear left",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_left_rear_quarter",
        name="Window rear quarter left",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_rear_windshield",
        name="window windshield rear",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_right_front",
        name="Window front right",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_right_rear",
        name="Window rear right",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_right_rear_quarter",
        name="Window rear quarter right",
        icon="mdi:car-door",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_sunroof",
        name="Window Sunroof",
        icon="mdi:car-select",
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
)
