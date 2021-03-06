"""
Support for MQTT roller shutters.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/rollershutter.mqtt/
"""
import logging

import homeassistant.components.mqtt as mqtt
from homeassistant.components.rollershutter import RollershutterDevice
from homeassistant.const import CONF_VALUE_TEMPLATE
from homeassistant.helpers import template

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['mqtt']

DEFAULT_NAME = "MQTT Rollershutter"
DEFAULT_QOS = 0
DEFAULT_PAYLOAD_UP = "UP"
DEFAULT_PAYLOAD_DOWN = "DOWN"
DEFAULT_PAYLOAD_STOP = "STOP"


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Add MQTT Rollershutter."""
    if config.get('command_topic') is None:
        _LOGGER.error("Missing required variable: command_topic")
        return False

    add_devices_callback([MqttRollershutter(
        hass,
        config.get('name', DEFAULT_NAME),
        config.get('state_topic'),
        config.get('command_topic'),
        config.get('qos', DEFAULT_QOS),
        config.get('payload_up', DEFAULT_PAYLOAD_UP),
        config.get('payload_down', DEFAULT_PAYLOAD_DOWN),
        config.get('payload_stop', DEFAULT_PAYLOAD_STOP),
        config.get(CONF_VALUE_TEMPLATE))])


# pylint: disable=too-many-arguments, too-many-instance-attributes
class MqttRollershutter(RollershutterDevice):
    """Representation of a roller shutter that can be controlled using MQTT."""

    def __init__(self, hass, name, state_topic, command_topic, qos,
                 payload_up, payload_down, payload_stop, value_template):
        """Initialize the roller shutter."""
        self._state = None
        self._hass = hass
        self._name = name
        self._state_topic = state_topic
        self._command_topic = command_topic
        self._qos = qos
        self._payload_up = payload_up
        self._payload_down = payload_down
        self._payload_stop = payload_stop

        if self._state_topic is None:
            return

        def message_received(topic, payload, qos):
            """A new MQTT message has been received."""
            if value_template is not None:
                payload = template.render_with_possible_json_value(
                    hass, value_template, payload)
            if payload.isnumeric() and 0 <= int(payload) <= 100:
                self._state = int(payload)
                self.update_ha_state()
            else:
                _LOGGER.warning(
                    "Payload is expected to be an integer between 0 and 100")

        mqtt.subscribe(hass, self._state_topic, message_received, self._qos)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the roller shutter."""
        return self._name

    @property
    def current_position(self):
        """Return current position of roller shutter.

        None is unknown, 0 is closed, 100 is fully open.
        """
        return self._state

    def move_up(self, **kwargs):
        """Move the roller shutter up."""
        mqtt.publish(self.hass, self._command_topic, self._payload_up,
                     self._qos)

    def move_down(self, **kwargs):
        """Move the roller shutter down."""
        mqtt.publish(self.hass, self._command_topic, self._payload_down,
                     self._qos)

    def stop(self, **kwargs):
        """Stop the device."""
        mqtt.publish(self.hass, self._command_topic, self._payload_stop,
                     self._qos)
