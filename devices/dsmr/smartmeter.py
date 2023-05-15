import serial
import threading
from . import datadefinitions
import re
import logging


class DSMRMeter(threading.Thread):
    def __init__(self, queue, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.queue = queue

    def preprocess(self, telegram):
        # Preprocess telegram to add totals of consumed and returned values
        consumed = 0.0
        returned = 0.0

        # Loop through the telegram line by line
        for element in telegram.split('\n'):
            try:
                val = re.match(r"1-0:1\.8\.1\((\d{6}\.\d{3})\*kWh\)", element).group(1)
                consumed = consumed + float(val)
            except Exception as e:
                logging.debug(e)
                pass

            try:
                val = re.match(r"1-0:1\.8\.2\((\d{6}\.\d{3})\*kWh\)", element).group(1)
                consumed = consumed + float(val)
            except Exception as e:
                logging.debug(e)
                pass

            try:
                val = re.match(r"1-0:2\.8\.1\((\d{6}\.\d{3})\*kWh\)", element).group(1)
                returned = returned + float(val)
            except Exception as e:
                logging.debug(e)
                pass

            try:
                val = re.match(r"1-0:2\.8\.2\((\d{6}\.\d{3})\*kWh\)", element).group(1)
                returned = returned + float(val)
            except Exception as e:
                logging.debug(e)
                pass

        # Format totals and append to telegram
        consumed = f"{consumed:010.3f}"
        consumed_line = f"1-0:1.8.3({consumed}*kWh)\n"
        telegram += consumed_line

        returned = f"{returned:010.3f}"
        returned_line = f"1-0:2.8.3({returned}*kWh)\n"
        telegram += returned_line

        return telegram

    def read_telegram(self):
        ser = serial.Serial()
        ser.baudrate = 115200
        ser.bytesize = serial.EIGHTBITS
        ser.parity = serial.PARITY_NONE
        ser.stopbits = serial.STOPBITS_ONE
        ser.xonxoff = 1
        ser.rtscts = 0
        ser.timeout = 12
        ser.port = self.serial_port

        try:
            ser.open()
        except serial.SerialException as e:
            logging.error(f'Error opening serial port {self.serial_port}: {e}')

        ser.flushInput()
        telegram = ''
        while '!' not in telegram:
            telegram += ser.readline().decode('ascii')

        processed_telegram = self.preprocess(telegram)

        ser.close()
        return processed_telegram

    def parse_telegram(self, telegram):
        if telegram != '':
            logging.debug(f'Telegram received: {telegram}')
            identified_telegram, value = datadefinitions.identify_telegram(telegram)
            tgr_desc = identified_telegram[datadefinitions.DESCRIPTION]
            tgr_val_search = re.search(identified_telegram[datadefinitions.REGEX], value)

            if tgr_val_search:
                tgr_val = tgr_val_search.group(1)
            else:
                tgr_val = ''

            # If the DATATYPE is a float or int, multiply the value by MULTIPLICATION
            d_type = identified_telegram[datadefinitions.DATATYPE]
            if d_type in ['float', 'int']:
                tgr_val = eval(d_type)(tgr_val) * eval(d_type)(identified_telegram[datadefinitions.MULTIPLICATION])

            # Check if data validation is necessary and value is not zero. Skip entry if requirements not met
            valid_telegram = True
            if identified_telegram[datadefinitions.DATAVALIDATION] == '1':
                if tgr_val is None or tgr_val == '' or tgr_val == 0:
                    logging.warning(f'Warning: Telegram {tgr_desc} has invalid value ({tgr_val}). Skipping...')
                    valid_telegram = False

            # Format and push the telegram onto the queue so other threads can pick it up
            if valid_telegram:
                # Format: [prefix, topic, tag, value, messagerate, datatype] (list)
                prefix = 'dsmr'
                topic = identified_telegram[datadefinitions.MQTT_TOPIC]
                tag = identified_telegram[datadefinitions.MQTT_TAG]

                message_rate = identified_telegram[datadefinitions.MESSAGERATE]
                datatype = identified_telegram[datadefinitions.DATATYPE]
                val = eval(datatype)(tgr_val)
                self.queue.put([prefix, topic, tag, val, message_rate])

    def run(self):
        logging.info("--- Starting P1 SmartMeter thread ---")
        while True:
            telegram = self.read_telegram()
            telegram_list = telegram.splitlines()
            for item in telegram_list:
                self.parse_telegram(item)
