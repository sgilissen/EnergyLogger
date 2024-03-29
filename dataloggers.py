import atexit
import threading
import logging
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
from datetime import datetime

logger = logging.getLogger(__name__)


class InfluxLogger(threading.Thread):
    def __init__(self, queue, url, token, org, bucket_id):
        super().__init__()
        self.queue = queue
        self.url = url
        self.token = token
        self.org = org
        self.bucket_id = bucket_id
        self.client = InfluxDBClient(
            url=self.url, token=self.token, org=self.org)

        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

        atexit.register(self.on_exit, self.client, self.write_api)

    def on_exit(self, db_client, write_api):
        write_api.__del__()
        db_client.__del__()
        # print("on_exit called")
        logger.info('Exiting...')

    def write(self, data):
        try:
            line_protocol = data.to_line_protocol()
            logging.debug(data)
            logging.debug(f'Line: {line_protocol}')
            self.write_api.write(bucket=self.bucket_id, org=self.org, record=line_protocol)
        except Exception as err:
            logger.error(f'Influx exception: {err}')

    def _format_line(self, prefix, topic, key, value):
        p = Point(f'{prefix}_{topic}').tag('location', 'lt').time(time=datetime.utcnow()).field(key, value)

        return p

    def run(self):
        logger.info('Starting InfluxDB Logger...')
        # Received format: [prefix, topic, key, value, messagerate] (list)

        # Set up a dict to hold temporary data (for timestamp purposes)
        last_msg = {}

        while True:
            item = self.queue.get()
            logger.debug(f'InfluxDB Logger received item: {item}')

            # Calculate message rate
            if int(item[4]) == 0:
                min_time_interval = -1
            else:
                min_time_interval = int(3600/int(item[4]))

            # Set the current timestamp (UNIX epoch as integer)
            current_ts = int((datetime.now() - datetime(1970, 1, 1)).total_seconds())
            prefix = item[0]
            topic = item[1]
            tag = item[2]
            value = item[3]

            if min_time_interval != -1:
                # If the message rate is not 0 (-1, as calculated above), update the temporary message dict
                if prefix not in last_msg:
                    last_msg[prefix] = {}
                    last_msg[prefix]['value'] = value
                    last_msg[prefix]['timestamp'] = current_ts
                    # Post to InfluxDB
                    self.write(self._format_line(prefix, topic, tag, value))

                else:
                    prev_ts = last_msg[prefix]['timestamp']
                    if current_ts >= prev_ts + min_time_interval:
                        last_msg[prefix]['value'] = value
                        last_msg[prefix]['timestamp'] = current_ts
                        # Post to InfluxDB
                        self.write(self._format_line(prefix, topic, tag, value))


class MQTTLogger(threading.Thread):
    def __init__(self, queue, mqtt_server, mqtt_port, mqtt_user, mqtt_password, mqtt_client_id):
        super().__init__()
        self.queue = queue
        self.mqtt_server = mqtt_server
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        self.mqtt_client_id = mqtt_client_id

    # MQTT callbacks
    def mqtt_on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            resultstr = "Success!"
        else:
            resultstr = f"Failed with result code {rc}"
        logger.info(f'Connecting to MQTT server... Result: {resultstr}')
        # client.subscribe("$SYS/#")

    def mqtt_publish(self, client, topic, msg):
        result = client.publish(topic, msg)
        status = result[0]
        if status == 0:
            logger.debug(f'MQTT: Published value ({msg}) to {topic}!')
        else:
            logger.warning(f'Unable to publish to MQTT topic {topic}! Message: {msg}')

    def run(self):
        logger.info('Starting MQTT Logger...')
        # Received format: [prefix, topic, tag, value, messagerate] (list)

        # Set up a dict to hold temporary data (for timestamp purposes)
        last_msg = {}

        # MQTT client
        mqtt_client = mqtt.Client(self.mqtt_client_id)
        mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)
        mqtt_client.on_connect = self.mqtt_on_connect
        mqtt_client.connect(self.mqtt_server, self.mqtt_port)

        mqtt_client.loop_start()

        while True:
            item = self.queue.get()
            logger.debug(f'MQTT Logger received item: {item}')

            # Calculate message rate
            if int(item[4]) == 0:
                min_time_interval = -1
            else:
                min_time_interval = int(3600/int(item[4]))

            # Set the current timestamp (UNIX epoch as integer)
            current_ts = int((datetime.now() - datetime(1970, 1, 1)).total_seconds())
            topic = f'{item[0]}/{item[1]}/{item[2]}'
            value = item[3]

            if min_time_interval != -1:
                # If the message rate is not 0 (-1, as calculated above), update the temporary message dict
                if topic not in last_msg:
                    last_msg[topic] = {}
                    last_msg[topic]['value'] = value
                    last_msg[topic]['timestamp'] = current_ts
                    # Post to MQTT
                    logger.debug(f'MQTT Publish: {topic}, {value}')
                    self.mqtt_publish(mqtt_client, topic, value)
                else:
                    prev_ts = last_msg[topic]['timestamp']
                    if current_ts >= prev_ts + min_time_interval:
                        last_msg[topic]['value'] = value
                        last_msg[topic]['timestamp'] = current_ts
                        # Post to MQTT
                        logger.debug(f'MQTT Publish: {topic}, {value}')
                        self.mqtt_publish(mqtt_client, topic, value)
