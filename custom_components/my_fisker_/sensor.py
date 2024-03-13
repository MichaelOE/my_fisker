"""Platform for sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FiskerEntityDescription, MyFiskerCoordinator
from .const import CLIMATE_CONTROL_SEAT_HEAT, DOMAIN, LIST_CLIMATE_CONTROL_SEAT_HEAT

_LOGGER = logging.getLogger(__name__)


class FiskerSensor(CoordinatorEntity, SensorEntity):
    # An entity using CoordinatorEntity.

    def __init__(
        self,
        coordinator: MyFiskerCoordinator,
        idx,
        sensor: FiskerEntityDescription,
        client,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        # self._sensor = sensor
        self._data = client
        self._coordinator = coordinator
        self.entity_description: FiskerEntityDescription = sensor
        self._attr_unique_id = f"{self._coordinator.data['vin']}_{sensor.key}"
        self._attr_name = f"{self._coordinator._alias} {sensor.name}"

        _LOGGER.info(self._attr_unique_id)

        if sensor.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_unit_of_measurement
        else:
            if "seat_heat" in self.entity_description.key:
                self._attr_options = LIST_CLIMATE_CONTROL_SEAT_HEAT
                self._attr_device_class = SensorDeviceClass.ENUM

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

        data_available = False

        self.update_travelstats()

        if "car_settings" in self.entity_description.key:
            try:
                value = "n/a"
                carSetting = self._coordinator.my_fisker_api.GetCarSettings()
                # key = self.entity_description.key.replace("car_settings_", "")

                value = self.entity_description.get_car_settings_value(carSetting)
                # value = self.findInArray(carSetting, key.replace("_updated", ""))
                if "_updated" in self.entity_description.key:
                    value = value["updated"]
                else:
                    value = value["value"]

                data_available = True
            except:
                _LOGGER.debug("car_settings not available")

            self._attr_native_value = value

        elif "travelstat" in self.entity_description.key:
            if "battery" in self.entity_description.key:
                value = self._coordinator.travelstats.GetTravelBatt()

            if "distance" in self.entity_description.key:
                value = self._coordinator.travelstats.GetTravelDist()

            if "duration" in self.entity_description.key:
                value = self._coordinator.travelstats.GetTravelTime()

            if "efficiency" in self.entity_description.key:
                value = self._coordinator.travelstats.GetEfficiency()

            self._attr_native_value = value

        else:
            value = self._coordinator.data[self.idx[1]]
            data_available = True

            if "seat_heat" in self.entity_description.key:
                self._attr_native_value = CLIMATE_CONTROL_SEAT_HEAT[value][0]
            else:
                self._attr_native_value = value

        self._attr_available = data_available
        self.async_write_ha_state()

    def update_travelstats(self):
        carStartedDriving = False
        carIsDriving = False
        carEndedDriving = False

        if self._coordinator.travelstats.vehicleParked is True:
            if (
                self._coordinator.travelstats.vehicleParked
                != self._coordinator.data["gear_in_park"]
            ):
                carStartedDriving = True

        if (
            self._coordinator.travelstats.vehicleParked is False
            and self._coordinator.data["gear_in_park"] is False
        ):
            carIsDriving = True

        if (
            self._coordinator.travelstats.vehicleParked is False
            and self._coordinator.data["gear_in_park"] is True
        ):
            carEndedDriving = True

        self._coordinator.travelstats.vehicleParked = self._coordinator.data[
            "gear_in_park"
        ]

        if carStartedDriving:
            self._coordinator.travelstats.Clear()

        if carStartedDriving or carIsDriving:
            # Get battery info
            if "battery_percent" in self.entity_description.key:
                prevBatt = self._attr_native_value

                # Save battery info
                if prevBatt != self._coordinator.data[self.idx[1]]:
                    self._coordinator.travelstats.AddBattery(
                        self._coordinator.data[self.idx[1]]
                    )

            # Get distance info
            if "battery_total_mileage_odometer" in self.entity_description.key:
                prevDist = self._attr_native_value

                # Save distance info
                if prevDist != self._coordinator.data[self.idx[1]]:
                    self._coordinator.travelstats.AddDistance(
                        self._coordinator.data[self.idx[1]]
                    )
        elif carEndedDriving:
            pass

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
    for sensor in SENSORS_DIGITAL_TWIN:
        if sensor.key == key:
            return sensor


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

    for sensor in SENSORS_CAR_SETTINGS:
        entities.append(FiskerSensor(coordinator, 100, sensor, my_Fisker_data))

    for sensor in SENSORS_TRAVELSTAT:
        entities.append(FiskerSensor(coordinator, 200, sensor, my_Fisker_data))

    # Add entities to Home Assistant
    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    # Code for setting up your platform inside of the event loop
    _LOGGER.debug("async_setup_platform")


SENSORS_DIGITAL_TWIN: tuple[SensorEntityDescription, ...] = (
    FiskerEntityDescription(
        key="battery_avg_cell_temp",
        name="Battery avg. cell temp",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_charge_type",
        name="Battery charge type",
        icon="mdi:car",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_max_miles",
        name="Battery max miles",
        icon="mdi:car",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_percent",
        name="Battery percent",
        icon="mdi:battery-70",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=PERCENTAGE,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_remaining_charging_time",
        name="Battery remaining charging time",
        icon="mdi:battery-clock-outline",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_remaining_charging_time_full",
        name="Battery remaining charging time full",
        icon="mdi:battery-clock-outline",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_state_of_charge",
        name="Battery state of charge",
        icon="mdi:car-electric",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="battery_total_mileage_odometer",
        name="Battery total mileage odometer",
        icon="mdi:counter",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_ambient_temperature",
        name="Ambient temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_cabin_temperature",
        name="Cabin temperature",
        icon="mdi:temperature-celsius",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_driver_seat_heat",
        name="Driver seat heating",
        icon="mdi:car-seat-heater",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_internal_temperature",
        name="Internal temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_passenger_seat_heat",
        name="Passenger seat heating",
        icon="mdi:car-seat-heater",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="climate_control_rear_defrost",
        name="Rear window defrost",
        icon="mdi:car-defrost-rear",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="ip",
        name="IP address",
        icon="mdi:ip",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="location_altitude",
        name="Location altitude",
        icon="mdi:altimeter",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="location_latitude",
        name="Location latitude",
        icon="mdi:map-marker-radius",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="location_longitude",
        name="Location longitude",
        icon="mdi:map-marker-radius",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="trex_version",
        name="Trex version",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="updated",
        name="Last updated",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="vehicle_speed_speed",
        name="Vehicle speed",
        icon="mdi:speedometer",
        device_class=SensorDeviceClass.SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="vin",
        name="VIN no",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_left_front",
        name="Window front left",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_left_rear",
        name="window rear left",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_left_rear_quarter",
        name="Window rear quarter left",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_rear_windshield",
        name="window windshield rear",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_right_front",
        name="Window front right",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_right_rear",
        name="Window rear right",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_right_rear_quarter",
        name="Window rear quarter right",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="windows_sunroof",
        name="Window Sunroof",
        icon="mdi:car-select",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
)

SENSORS_CAR_SETTINGS: tuple[SensorEntityDescription, ...] = (
    FiskerEntityDescription(
        key="car_settings_os_version",
        name="OS version",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="car_settings_os_version_updated",
        name="OS version date",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="car_settings_flashpack_number",
        name="Flash pack no",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="car_settings_flashpack_number_updated",
        name="Flash pack no date",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="car_settings_BODY_COLOR",
        name="Body color",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="car_settings_DELIVERY_DESTINATION",
        name="Delivery country",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
)

SENSORS_TRAVELSTAT: tuple[SensorEntityDescription, ...] = (
    FiskerEntityDescription(
        key="travelstat_distance",
        name="Trip distance",
        icon="mdi:car-info",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="travelstat_duration",
        name="Trip duration",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="travelstat_battery",
        name="Trip energy",
        icon="mdi:car-info",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda data, key: data[key],
    ),
    FiskerEntityDescription(
        key="travelstat_efficiency",
        name="Trip eficiency",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
)