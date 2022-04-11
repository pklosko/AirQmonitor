#!/usr/bin/env python3

import os
import sys
import atexit
import signal
import logging
import threading
import logging.handlers
from time import sleep
from sps30 import SPS30
from sht40 import SHT40
from bmp280 import BMP280
#from myIoT.myIoT import myIOT
from sensorComm.sensorComm import sensorCommunity

PERIOD = 3

# Sensors settings
SHT_BUS = 4
SHT_PRECISION = 'hi' # [ 'hi' | 'mid' | 'low' ]
SPS_BUS = 3
SPS_AUTO_CLEANING_DAYS = 5

# Path settings
BASE_DIR     = "/home/pi/AirQmonitor"
LOG_FILENAME = "/var/log/airqmon.log"     # File name, set propper chmod
LOG_LEVEL    = logging.INFO               # Could be e.g. "INFO", DEBUG" or "WARNING"

#API keys etc.
# SensorsCommunity
SC_SENSOR_ID  = "raspi-xxxxxx"
SC_SHT_PIN    = 11
SC_SPS_PIN    = 1
# PK IOT Platform (simply HTTP GET, vals in QUERY STRING)
IOT_USER_AGENT = "rpi/Python/AirQmonitor"


# Logger
logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
handler   = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def print(*args):
  msg = ""
  for arg in args:
    msg += str(arg) + " "
  logger.info(msg)


def notDaemon():
  try:
    notD = (os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()))
  except Exception as e :
    notD = True
  return notD


def create_daemon():
  try:
    pid = os.fork()
    print("Fork : " + str(pid))
    if pid > 0:
      sys.exit(0)

  except OSError as e:
    print("Unable to fork")
    sys.exit(1)


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    create_daemon()
    PID=os.getpid()
    print("AirQmonitor started :", PID )

    def sps_stop():
        print("===========  STOP MEASUREMENT AND EXIT  ===========")
        sps_sensor.stop_measurement_and_close()

    def sigusr1_handler(signum, frame):
        print("===========  START CLEANING for 10sec  ===========")
        sps_sensor.start_fan_cleaning()
        print("===========  CLEANING FINISHED  ===========")

    atexit.register(sps_stop)
    signal.signal(signal.SIGUSR1, sigusr1_handler)

    sps_sensor = SPS30(SPS_BUS)
    sht_sensor = SHT40(SHT_BUS)
    bmp_sensor = BMP280(SHT_BUS)
#    iot = myIOT(PERIOD, IOT_USER_AGENT)
    sc = sensorCommunity(SC_SENSOR_ID)

    print("===========  SHT40  ===========")
    sht_serial_number   = sht_sensor.serial_number()
    print(f"SHT Serial number: {sht_serial_number}")
    print(f"SHT data HI RES  : {sht_sensor.read_measurement('hi')}")
    print(f"SHT data MID RES : {sht_sensor.read_measurement('mid')}")
    print(f"SHT data LO RES  : {sht_sensor.read_measurement('low')}")
    print("")

    print("===========  SPS30  ===========")
    sps_firmware_version = sps_sensor.firmware_version()
    sps_product_type     = sps_sensor.product_type()
    sps_serial_number    = sps_sensor.serial_number()
    print(f"SPS Firmware version: {sps_firmware_version}")
    print(f"SPS Product type    : {sps_product_type}")
    print(f"SPS Serial number   : {sps_serial_number}")
    sps_status_register  = sps_sensor.read_status_register()
    print(f"SPS Status register : {sps_status_register}")
    print(f"SPS Set auto cleaning interval: {sps_sensor.write_auto_cleaning_interval_days(SPS_AUTO_CLEANING_DAYS)} sec")
    sps_auto_cleaning_interval = sps_sensor.read_auto_cleaning_interval('d')
    print(f"SPS Auto cleaning interval    : {sps_auto_cleaning_interval} days")

    sps_sensor.start_measurement()
    print(f"SPS data: {sps_sensor.read_measurement()}")

    print("")

    print("===========  BMP280 ============")
    print(f"BMP Device ID    : {bmp_sensor.device_id()}")
    print(f"BMP MEAS_REG     : {bmp_sensor.meas_reg()}")
    print(f"BMP CTRL_REG     : {bmp_sensor.ctrl_reg()}")
    print(f"BMP SET MEAS_REG : {bmp_sensor.set_meas_reg()}")
    print(f"BMP SET CTRL_REG : {bmp_sensor.set_ctrl_reg()}")
    print(f"BMP MEAS_REG     : {bmp_sensor.meas_reg()}")
    print(f"BMP CTRL_REG     : {bmp_sensor.ctrl_reg()}")
    print(f"BMPCALIB_REG     : {bmp_sensor.calib_reg()}")

    sensor_info  = f"SHT40[{sht_serial_number}]+SPS30[{sps_serial_number}/v.{sps_firmware_version}/{sps_product_type}/{sps_auto_cleaning_interval}d/"
    for key in sps_status_register:
        sensor_info = sensor_info + "-" + sps_status_register[key]
    sensor_info = sensor_info + "]"

    bmp_sensor.read_calib_data(bmp_sensor.calib_reg())

    print("")
    print("=== WAITING 30 sec FOR DATA STABILIZATION ===")
    sleep(30)
    print("===========  LOOP  ===========")

    while True:
        try:
            while(sps_sensor.is_cleaning() == 1):
                print("=========== CLEANING IN PROCESS - WAIT ===========")
                sleep(1)
            sensors_values = dict(sht_sensor.read_values(SHT_PRECISION))
            sensors_values.update(bmp_sensor.read_values())
            sc.create_json(sensors_values)
            print(sc.post(SC_SHT_PIN))

            sensors_values.update(sps_sensor.read_values())
            sc.create_json(sensors_values)
            print(sc.post(SC_SPS_PIN))

#            iot.values_to_query_str(sensors_values)
#            iot.sensor_info  = sensor_info
#            print(iot.push())

            sps_sensor.stop_measurement()
            tim_thr = threading.Timer((int((PERIOD*60)-45)), sps_sensor.start_measurement, args=()).start()

            sleep(PERIOD*60)

        except KeyboardInterrupt:
            sys.exit()

        except Exception as e :
            print("===========  ERROR - EXIT  ===========")
            sys.exit(1)
