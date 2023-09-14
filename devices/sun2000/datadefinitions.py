"""
DSMR Dictionary:
dsmr version 5

Adapted from https://raw.githubusercontent.com/hansij66/dsmr2mqtt/main/dsmr50.py

index:
[description, mqtt_topic, regex received data, datatype, multiply factor, maxrate]]

INDEX = {
  "DESCRIPTION",
  "MQTT_TOPIC",
  "MQTT_TAG",
  "REGEX",
  "DATATYPE",
  "MULTIPLICATION",
  "MAXRATE"
}


        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

DESCRIPTION = 0       # Description, specify units of measure between []
MQTT_TOPIC = 1        # MQTT base topic; will be packed in a json message
MQTT_TAG = 2          # MQTT tag in json message; Need to be unique per topic
REGEX = 3             # python regex to filter extract data from dsmr telegram
DATATYPE = 4          # data type of data (int, float, str)
DATAVALIDATION = 5    # "0" (zero allowed), "1" (zero not allowed); validate data range; ignore if not valid;
MULTIPLICATION = 6    # In case of float of int, multiply factor (e.g. 1000 is unit is kW, and our messages are in W)
MESSAGERATE = 0       # Maximum number of messages per hour (0: none, 1: 1 per hour, 3600: limit to 1 per second)


def get_device_status_string(status):
    switcher = {
        0x0000: 'Standby: initializing',
        0x0001: 'Standby: detecting insulation resistance',
        0x0002: 'Standby: detecting irradiation',
        0x0003: 'Standby: drid detecting',
        0x0100: 'Starting',
        0x0200: 'On-grid (Off-grid mode: running)',
        0x0201: 'Grid connection: power limited (Off-grid mode: running: power limited)',
        0x0202: 'Grid connection: self-derating (Off-grid mode: running: self-derating)',
        0x0300: 'Shutdown: fault',
        0x0301: 'Shutdown: command',
        0x0302: 'Shutdown: OVGR',
        0x0303: 'Shutdown: communication disconnected',
        0x0304: 'Shutdown: power limited',
        0x0305: 'Shutdown: manual startup required',
        0x0306: 'Shutdown: DC switches disconnected',
        0x0307: 'Shutdown: rapid cutoff',
        0x0308: 'Shutdown: input underpower',
        0x0401: 'Grid scheduling: cos F-P curve',
        0x0402: 'Grid scheduling: Q-U curve',
        0x0403: 'Grid scheduling: PF-U curve',
        0x0404: 'Grid scheduling: dry contact',
        0x0405: 'Grid scheduling: Q-P curve',
        0x0500: 'Spot-check ready',
        0x0501: 'Spot-checking',
        0x0600: 'Inspecting',
        0x0700: 'AFCI self check',
        0x0800: 'I-V scanning',
        0x0900: 'DC input detection',
        0x0a00: 'Running: off-grid charging',
        0xa000: 'Standby: no irradiation'
    }

    return switcher.get(status, "Invalid status")