import serial
import time
import threading
from . import datadefinitions
import re
import logging
import minimalmodbus
import functools


class Sun2000(threading.Thread):
    def __init__(self, queue, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.serial_baud = 9600
        self.queue = queue
        self.prefix = 'solar'
        self.slave_address = 1
        self.instrument = minimalmodbus.Instrument(
            self.serial_port, self.slave_address)
        self.instrument.serial.baudrate = self.serial_baud
        self.instrument.serial.timeout = 0.2
    
    def retry_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retry_count = 500
            total_count = 0
            error_count = 0
            result = None
            logging.info(func)

            while result == None and retry_count > 0:
                total_count += 1
                try:
                    result = func(*args, **kwargs)
                except Exception as err:
                    error_count += 1
                    retry_count -= 1
                    time.sleep(0.1)
                    if retry_count == 0:
                        logging.error('Last exception message: {}'.format(err))
                        error_rate = int(error_count/total_count*100)
                        logging.error(f'Error rate: {error_rate}%')
            return result
        return wrapper
    
    @retry_decorator
    def get_model(self):
        return str(self.instrument.read_string(30000, 15))
    
    @retry_decorator
    def get_model_id(self):
        return self.instrument.read_register(30070)

    @retry_decorator
    def get_pv_strings_number(self):
        return self.instrument.read_register(30071)

    @retry_decorator
    def get_pv_voltage(self, pv_string_no):
        return self.instrument.read_register(32014 + 2 * pv_string_no, 1, signed=True)

    @retry_decorator
    def get_pv_current(self, pv_string_no):
        return self.instrument.read_register(32015 + 2 * pv_string_no, 2, signed=True)

    @retry_decorator
    def get_phase_a_voltage(self):
        return self.instrument.read_register(32069, 1)

    @retry_decorator
    def get_phase_b_voltage(self):
        return self.instrument.read_register(32070, 1)

    @retry_decorator
    def get_phase_c_voltage(self):
        return self.instrument.read_register(32071, 1)

    @retry_decorator
    def get_phase_a_current(self):
        return self.instrument.read_register(32072, 3, signed=True)

    @retry_decorator
    def get_phase_b_current(self):
        return self.instrument.read_register(32074, 3, signed=True)

    @retry_decorator
    def get_phase_c_current(self):
        return self.instrument.read_register(32076, 3, signed=True)

    @retry_decorator
    def get_input_power(self):
        return self.instrument.read_long(32064, 3, signed=True)

    @retry_decorator
    def get_active_power(self):
        return self.instrument.read_long(32080, 3, signed=True)

    @retry_decorator
    def get_reactive_power(self):
        return self.instrument.read_long(32082, 3, signed=True)

    @retry_decorator
    def get_power_factor(self):
        return self.instrument.read_register(32084, 3, signed=True)

    @retry_decorator
    def get_efficiency(self):
        return self.instrument.read_register(32086, 2)

    @retry_decorator
    def get_day_power(self):
        return self.instrument.read_long(32078, 3, signed=True)

    @retry_decorator
    def get_total_power(self):
        return self.instrument.read_long(32106, 3, signed=True)

    @retry_decorator
    def get_internal_temp(self):
        return self.instrument.read_register(32087, 1, signed=True)
    
    @retry_decorator
    def get_device_status(self):
        return self.instrument.read_register(32089)

    def log_message(self, topic, tag, datatype, val, message_rate):
        val = eval(datatype)(val)
        self.queue.put([self.prefix, topic, tag, val, message_rate])
        
    def run(self):
        logging.info(f"Starting Sun2000 (device on {self.serial_port})...")
        self.model_id = self.get_model_id()
        logging.info(f'Model ID: {self.model_id}')

        self.model = self.get_model().rstrip('\x00')
        logging.info(f'Model: {self.model}')

        self.pv_string_count = self.get_pv_strings_number()
        logging.info(f'PV String count: {self.pv_string_count}')
        
        self.device_status_code = None
        self.device_status_string = None
        self.internal_temp = None
        
        
        while True:
            device_status_code = self.get_device_status()
            device_status_string = datadefinitions.get_device_status_string(device_status_code)
            internal_temp = self.get_internal_temp()
            
            
            if (self.device_status_code != device_status_code):
                self.device_status_code = device_status_code
                self.device_status_string = device_status_string
                logging.info(f'Device status: {self.device_status_code} {self.device_status_string}')
                
                self.log_message('system', 'status_code', 'int', self.device_status_code, 3600)
                self.log_message('system', 'status_string', 'str', self.device_status_string, 3600)

                

            if (self.internal_temp != internal_temp):
                # topic, tag, datatype, data, message_rate
                self.internal_temp = internal_temp

                self.log_message('system', 'internal_temp', 'float', internal_temp, 3600)

                logging.info(f'Device temperature: {self.internal_temp}')

            if (0xa000 == device_status_code):
                time.sleep(10)
                continue

            pv = {}
            
            for pv_string_no in range(self.pv_string_count):
                pv[f'pv{pv_string_no}_voltage'] = self.get_pv_voltage(
                    pv_string_no + 1)
                pv[f'pv{pv_string_no}_current'] = self.get_pv_current(
                    pv_string_no + 1)

            
            elec_data = {
                **pv,
                'phase_a_voltage': self.get_phase_a_voltage(),
                'phase_b_voltage': self.get_phase_b_voltage(),
                'phase_b_voltage': self.get_phase_c_voltage(),
                'phase_a_current': self.get_phase_a_current(),
                'phase_b_current': self.get_phase_b_current(),
                'phase_c_current': self.get_phase_c_current(),
                'input_power': self.get_input_power(),
                'active_power': self.get_active_power(),
                'reactive_power': self.get_reactive_power(),
                'power_factor': self.get_power_factor(),
                'efficiency': self.get_efficiency(),
                'day_power': self.get_day_power(),
                'total_power': self.get_total_power()
            }
            
            # Dictionary comprehension to change "None" to 0.0, as these are all numeric (float) values
            elec_data_cleaned = {k: v or 0.0 for (k, v) in elec_data.items()}
            
            # Loop over the dictionary and log each entry
            for entry in elec_data_cleaned:
                self.log_message('metrics', entry, 'float', elec_data_cleaned[entry], 3600)
            
            
            
