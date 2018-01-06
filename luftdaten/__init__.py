"""
Copyright (c) 2017-2018 Fabian Affolter <fabian@affolter-engineering.ch>

Licensed under MIT. All rights reserved.
"""
import asyncio
import logging

import aiohttp
import async_timeout

from . import exceptions

_LOGGER = logging.getLogger(__name__)
_RESOURCE = 'https://api.luftdaten.info/v1'

VOLUME_MICROGRAMS_PER_CUBIC_METER = 'µg/m3'

SENSOR_TEMPERATURE = 'temperature'
SENSOR_HUMIDITY = 'humidity'
SENSOR_PM10 = 'P1'
SENSOR_PM2_5 = 'P2'

SENSOR_TYPES = {
    SENSOR_TEMPERATURE: ['Temperature', '°C'],
    SENSOR_HUMIDITY: ['Humidity', '%'],
    SENSOR_PM10: ['PM10', VOLUME_MICROGRAMS_PER_CUBIC_METER],
    SENSOR_PM2_5: ['PM2.5', VOLUME_MICROGRAMS_PER_CUBIC_METER]
}


class Luftdaten(object):
    """A class for handling connections from Luftdaten.info."""

    def __init__(self, sensor_id, loop, session):
        """Initialize the connection."""
        self._loop = loop
        self._session = session
        self.sensor_id = sensor_id
        self.data = None
        self.values = {
                'humidity': None,
                'P1': None,
                'P2': None,
                'pressure': None,
                'temperature': None,
            }
        self.meta = {}

    @asyncio.coroutine
    def async_get_data(self):
        url = '{}/{}/{}/'.format(_RESOURCE, 'sensor', self.sensor_id)

        try:
            with async_timeout.timeout(5, loop=self._loop):
                response = yield from self._session.get(url)

            _LOGGER.debug(
                "Response from luftdaten.info: %s", response.status)
            data = yield from response.json()
            _LOGGER.debug(data)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Can not load data from luftdaten.info")
            raise exceptions.LuftdatenConnectionError()

        print(data)
        try:
            sensor_data = sorted(
                data, key=lambda timestamp: timestamp['timestamp'],
                reverse=True)[0]
            print(sensor_data)
            for entry in sensor_data['sensordatavalues']:
                for measurement in self.values.keys():
                    if measurement == entry['value_type']:
                        self.values[measurement] = float(entry['value'])

            self.meta['sensor_id'] = self.sensor_id
            self.meta['longitude'] = float(sensor_data['location']['longitude'])
            self.meta['latitude'] = float(sensor_data['location']['latitude'])
        except (TypeError, IndexError):
            raise exceptions.LuftdatenError()
