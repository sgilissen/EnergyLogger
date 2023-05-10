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
MESSAGERATE = 7       # Maximum number of messages per hour (0: none, 1: 1 per hour, 3600: limit to 1 per second)


def identify_telegram(telegram):
    definition = {
        # System messages
        "1-3:0.2.8":
            ["DSMR Version meter", "system", "dsmr_version", "^.*\((.*)\)", "str", "0", "1", "0"],
        "0-0:96.1.1":
            ["Equipment identifier", "el", "serial", "^.*\((.*)\)", "str", "1", "1", "1"],
        "0-1:96.1.1":
            ["Equipment identifier", "gas", "serial", "^.*\((.*)\)", "str", "1", "1", "1"],
        "0-0:96.1.4":
            ["Version information", "system", "system_version", "^.*\((.*)\)", "str", "0", "1", "0"],
        "0-0:96.13.0":
            ["Text message (future use)", "system", "text_mesage", "^.*\((.*)\)", "str", "0", "1", "0"],

        "1-0:31.4.0":
            ["Fuse supervision treshold", "el", "fuse_treshold", "^.*\((.*)\*A\)", "str", "0", "1", "0"],
        "0-0:17.0.0":
            ["Limiter treshold", "el", "limiter_treshold", "^.*\((.*)\*kW\)", "str", "0", "1", "0"],
        "0-0:96.3.10":
            ["Breaker state", "el", "breaker_state", "^.*\((.*)\)", "int", "0", "1", "12"],
        "0-1:24.1.0":
            ["Device type", "el", "device_type", "^.*\((.*)\)", "int", "0", "1", "0"],

        "0-0:1.0.0":
            ["Timestamp [s]", "el", "timestamp", "^.*\((.*)S\)", "int", "1", "1", "0"],
        "0-0:96.7.21":
            ["Power failures amount", "el", "power_failures", "^.*\((.*)\)", "int", "0", "1", "60"],
        "0-0:96.7.9":
            ["Long power failures amount", "el", "long_power_failures", "^.*\((.*)\)", "int", "0", "1", "60"],
        "0-0:96.14.0":
            ["Tariff indicator electricity", "el", "tariff_indicator", "^.*\((.*)\)", "int", "0", "1", "0"],
        "1-0:21.7.0":
            ["Power usage L1 [W]", "el", "P1_consumed", "^.*\((.*)\*kW\)", "float", "0", "1000", "60"],
        "1-0:41.7.0":
            ["Power usage L2 [W]", "el", "P2_consumed", "^.*\((.*)\*kW\)", "float", "0", "1000", "60"],
        "1-0:61.7.0":
            ["Power usage L3 [W]", "el", "P3_consumed", "^.*\((.*)\*kW\)", "float", "0", "1000", "60"],
        "1-0:22.7.0":
            ["Power generation L1 [W]", "el", "P1_generated", "^.*\((.*)\*kW\)", "float", "0", "1000", "60"],
        "1-0:42.7.0":
            ["Power generation L2 [W]", "el", "P2_generated", "^.*\((.*)\*kW\)", "float", "0", "1000", "60"],
        "1-0:62.7.0":
            ["Power generation L3 [W]", "el", "P3_generated", "^.*\((.*)\*kW\)", "float", "0", "1000", "60"],
        "1-0:1.7.0":
            ["Total power usage [W]", "el", "p_consumed", "^.*\((.*)\*kW\)", "float", "0", "1000", "60"],
        "1-0:2.7.0":
            ["Total power generation [W]", "el", "p_generated", "^.*\((.*)\*kW\)", "float", "0", "1000", "60"],

        # 0-1:24.2.1 is presumably for the Netherlands. 0-1:24.2.3 is for Belgium.
        "0-1:24.2.1":
            ["Gas consumption [m\u00b3]", "gas", "gas_consumed", "^.*\((.*)\*m3\)", "float", "1", "1000", "12"],
        "0-1:24.2.3":
            ["Gas consumption [m\u00b3]", "gas", "gas_consumed", "^.*\((.*)\*m3\)", "float", "1", "1000", "12"],
        "0-1:96.1.0":
            ["Equipment Identifier", "gas", "serial", "^.*\(\d{26}(.*)\)", "str", "1", "1", "1"],

        "1-0:1.8.1":
            ["EL consumed (Tariff 1)[Wh]", "el", "el_consumed1", "^.*\((.*)\*kWh\)", "float", "1", "1000", "12"],
        "1-0:1.8.2":
            ["EL consumed (Tariff 2)[Wh]", "el", "el_consumed2", "^.*\((.*)\*kWh\)", "float", "1", "1000", "12"],
        "1-0:2.8.1":
            ["EL returned (Tariff 1)[Wh]", "el", "el_returned1", "^.*\((.*)\*kWh\)", "float", "1", "1000", "12"],
        "1-0:2.8.2":
            ["EL returned (Tariff 2)[Wh]", "el", "el_returned2", "^.*\((.*)\*kWh\)", "float", "1", "1000", "12"],

        # Virtual, non-existing in dsmr telegram & specification, to sum tariff 1 & 2 to a single message
        "1-0:1.8.3":
            ["EL consumed (total)[Wh]", "el", "el_consumed", "^.*\((.*)\*kWh\)", "float", "1", "1000", "12"],
        "1-0:2.8.3":
            ["EL returned (total)[Wh]", "el", "el_returned", "^.*\((.*)\*kWh\)", "float", "1", "1000", "12"],

        "1-0:32.7.0":
            ["Voltage L1 [V]", "el", "voltage_L1", "^.*\((.*)\*V\)", "float", "0", "1", "900"],
        "1-0:52.7.0":
            ["Voltage L2 [V]", "el", "voltage_L2", "^.*\((.*)\*V\)", "float", "0", "1", "900"],
        "1-0:72.7.0":
            ["Voltage L3 [V]", "el", "voltage_L3", "^.*\((.*)\*V\)", "float", "0", "1", "900"],
        "1-0:31.7.0":
            ["Current L1 [A]", "el", "current_L1", "^.*\((.*)\*A\)", "float", "0", "1", "900"],
        "1-0:51.7.0":
            ["Current L2 [A]", "el", "current_L2", "^.*\((.*)\*A\)", "float", "0", "1", "900"],
        "1-0:71.7.0":
            ["Current L3 [A]", "el", "current_L3", "^.*\((.*)\*A\)", "float", "0", "1", "900"],

        "1-0:32.36.0":
            ["Voltage swells L1", "el", "L1_swells", "^.*\((.*)\)", "float", "0", "1", "12"],
        "1-0:52.36.0":
            ["Voltage swells L2", "el", "L2_swells", "^.*\((.*)\)", "float", "0", "1", "12"],
        "1-0:72.36.0":
            ["Voltage swells L3", "el", "L3_swells", "^.*\((.*)\)", "float", "0", "1", "12"],
        "1-0:32.32.0":
            ["Voltage sags L1", "el", "L1_sags", "^.*\((.*)\)", "float", "0", "1", "12"],
        "1-0:52.32.0":
            ["Voltage sags L2", "el", "L2_sags", "^.*\((.*)\)", "float", "0", "1", "12"],
        "1-0:72.32.0":
            ["Voltage sags L3", "el", "L3_sags", "^.*\((.*)\)", "float", "0", "1", "12"],

        "1-0:1.4.0":
            ["Positive active demand in a current demand period", "el",
             "pos_act_demand", "^.*\((.*)\*kW\)", "float", "0", "1", "12"],
        "0-0:98.1.0":
            ["Maximum demand – Active energy import of the last 13 months", "el",
             "max_demand_13months", "^.*\((.*)\*kW\)", "float", "0", "1", "1"],
        "1-0:1.6.0":
            ["Positive active maximum demand (A+) total", "el", "pos_max_demand",
             "^.*\((.*)\*kW\)", "float", "0", "1", "60"],
        "0-1:24.4.0":
            ["Valve state", "gas", "valve_state", "^.*\((.*)\)", "int", "0", "1", "60"],

        # Custom telegram codes for checksum purposes, etc.
        "999-999:0.0":
            ["Checksum", "system", "checksum", "^.*\((.*)\)", "str", "0", "1", "0"],
        "999-999:0.1":
            ["Equipment provider", "system", "provider", "^.*\((.*)\)", "str", "0", "1", "0"],
        "999-999:1.0":
            ["Empty line", "system", "empty_line", "^.*\((.*)\)", "str", "0", "1", "0"]

    }

    # Split into list, get the first item in the list as the identifier.
    telegram_list = telegram.split('(')
    telegram_code = telegram_list[0]
    if str(telegram_code).startswith('!'):
        # Checksum, so we'll use a custom telegram code (see dict above)
        telegram_value = telegram_code.replace('!', '')
        telegram_code = "999-999:0.0"

    elif str(telegram_code).startswith('/'):
        # Provider code, so we'll use a custom telegram code (see dict above)
        telegram_value = telegram_code
        telegram_code = "999-999:0.1"

    else:
        # Remove identifier from the telegram so we keep just the value
        telegram_value = telegram.replace(telegram_code, '')

    # telegram_value = telegram.split('(')[1].replace(')', '')
    # print(f'------ Parsed telegram {telegram}: telegram_code: {telegram_code} - value: {telegram_value}')

    return definition.get(telegram_code, ["Invalid or unknown DSMR telegram",
                                          "errors", "err", "", "str", "0", "0", "0"]), telegram_value
