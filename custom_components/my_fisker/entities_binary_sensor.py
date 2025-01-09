"""All binary_sensor entities."""

from homeassistant.components.sensor import SensorEntityDescription

from . import FiskerSensorEntityDescription

BINARY_SENSORS: tuple[SensorEntityDescription, ...] = (
    FiskerSensorEntityDescription(
        key="climate_control_steering_wheel_heat",
        name="Steering wheel heat",
        icon="mdi:steering",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="door_locks_all",
        name="Door locks all",
        icon="mdi:car-door-lock",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="door_locks_driver",
        name="Door locks driver",
        icon="mdi:car-door-lock",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="doors_hood",
        name="Doors hood",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="doors_left_front",
        name="Door left front",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="doors_left_rear",
        name="Door left rear",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="doors_right_front",
        name="Door right front",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="doors_right_rear",
        name="Door right rear",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="doors_trunk",
        name="Door trunk",
        icon="mdi:car-door",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="gear_in_park",
        name="Gear in park",
        icon="mdi:car-brake-parking",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="online",
        name="Online State",
        icon="mdi:car-connected",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="online_hmi",
        name="Online hmi",
        icon="mdi:car-connected",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    FiskerSensorEntityDescription(
        key="vehicle_ready_state_is_vehicle_ready",
        name="Vehicle Ready",
        icon="mdi:car-info",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
)
