import queue
import logging
import os
import sys
import configparser

import dataloggers
from devices.dsmr import smartmeter

_config = configparser.ConfigParser()


def check_config():
    if not os.path.exists('config.cfg'):
        _config['MQTT'] = {
            'Server': '!CHANGEME',
            'Port': '!CHANGEME',
            'User': '!CHANGEME',
            'Password': '!CHANGEME',
        }

        _config['DEVICES'] = {
            'DSMRPort': '!CHANGEME',
            'SUN2KPort': '!CHANGEME'
        }

        _config['INFLUXDB'] = {
            'URL': '!CHANGEME',
            'Token': '!CHANGEME',
            'BucketID': '!CHANGEME',
            'Org': '!CHANGEME'
        }

        _config.write(open('config.cfg', 'w'))
        logging.error('Config file does not exist! New config file created.'
                      ' Please modify config.cfg with the appropriate settings')
        return False
    else:
        _config.read('config.cfg')

        for section in _config.sections():
            if any(v == '!CHANGEME' for k, v in iter(_config.items(section))):
                logging.error(f'Please check the config file {section} section.')
                return False
            else:
                return True


def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logging.info('Welcome to EnergyLogger --- Starting threads')

    # Check config, if config is invalid, exit.
    if not check_config():
        sys.exit()

    # Communication queue
    _q = queue.Queue()
    # Set up threads
    t_mqtt = dataloggers.MQTTLogger(
        _q,
        _config['MQTT']['Server'],
        int(_config['MQTT']['Port']),
        _config['MQTT']['User'],
        _config['MQTT']['Password'],
        'solar_pi'
    )
    t_dsmr = smartmeter.DSMRMeter(_q, _config['DEVICES']['dsmrport'])

    t_mqtt.start()
    t_dsmr.start()


if __name__ == "__main__":
    main()

