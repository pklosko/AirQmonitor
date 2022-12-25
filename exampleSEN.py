import sys
import json
import atexit
from time import sleep

from sen5x import SEN5x
from bmp280 import BMP280
from sensorComm.sensorComm import sensorCommunity


PERIOD = 3  #seconds

SEN_BUS = 4                 # SEN54 i2c bus
SEN_AUTO_CLEANING_DAYS = 5  # set auto cleaning interval to 5 days

BME_BUS = 4

# SensorsCommunity
SC_SENSOR_ID  = "your-sensorid"
SC_SHT_PIN    = 11
SC_SPS_PIN    = 1



if __name__ == "__main__":

# Stop measurement before exit
    def sen_stop():
        print("===========  EXIT  ===========")
        sen_sensor.stop_measurement_and_close()
    atexit.register(sen_stop)

# Init SEN class, set i2c bus
    sen_sensor = SEN5x(SEN_BUS)
    sc = sensorCommunity(SC_SENSOR_ID)

# print some info
    print("===========  SEN5x  ===========")
    print(f"SEN Firmware version          : {sen_sensor.firmware_version()}")
    print(f"SEN Product name              : {sen_sensor.product_name()}")
    print(f"SEN Serial number             : {sen_sensor.serial_number()}")
    print(f"SEN Status register           : {sen_sensor.read_status_register()}")
    print(f"SEN Auto cleaning interval    : {sen_sensor.read_auto_cleaning_interval('d')} days")
    print(f"SEN Warm Start parameter      : {sen_sensor.read_warm_start_param()}")
    print(f"SEN NOX Algo Tunning param    : {sen_sensor.read_nox_tunning_param()}")
    print(f"SEN VOC Algo Tunning param    : {sen_sensor.read_voc_tunning_param()}")
    print(f"SEN Thermo compens param      : {sen_sensor.read_thermo_compensation_param()}")

# Start SEN54 meaasurement
    sen_sensor.start_measurement()
    print(f"SEN data                      : {sen_sensor.read_measurement()}")

    print("")
    print("=== WAITING 30 sec FOR DATA STABILIZATION ===")
    sleep(30)
    print("===========  LOOP  ===========")

# Load all values in one list/dist and print (or use according to your discretion)
    while True:
        try:
            sensors_values = dist(bmp_sensor.read_values())
            sc.create_json(sensors_values)
            print(sc.post(SC_SHT_PIN))

            sensors_values.update(sen_sensor.read_values())
            sc.create_json(sensors_values)
            print(sc.post(SC_SPS_PIN))

            print(json.dumps(sensors_values, indent=2))

            sleep(PERIOD*60)

        except KeyboardInterrupt:
            sys.exit()

