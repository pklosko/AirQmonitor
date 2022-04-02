import sys
import json
import atexit
from time import sleep

from sps30 import SPS30
from sht40 import SHT40
from sensorComm.sensorComm import sensorCommunity

PERIOD = 3  #minutes

SHT_BUS = 4                 # SHT40 i2c bus
SHT_PRECISION = 'hi'        # SHT40 precision ['hi' | 'mid' | 'low']

SPS_BUS = 3                 # SPS30 i2c bus
SPS_AUTO_CLEANING_DAYS = 5  # SPS30 auto clearing period

# SensorsCommunity
SC_SENSOR_ID  = "your-sensorid"
SC_SHT_PIN    = 11
SC_SPS_PIN    = 1


if __name__ == "__main__":

# Stop measurement before exit
    def sps_stop():
        print("===========  EXIT  ===========")
        sps_sensor.stop_measurement()
    atexit.register(sps_stop)

# Init SPS & SHT class, set i2c bus
    sps_sensor = SPS30(SPS_BUS)
    sht_sensor = SHT40(SHT_BUS)
    sc = sensorCommunity(SC_SENSOR_ID)

# Print some info
    print("===========  SHT40  ===========")
    print(f"SHT Serial number: {sht_sensor.serial_number()}")
    print(f"SHT data HI RES  : {sht_sensor.read_measurement('hi')}")
    print(f"SHT data MID RES : {sht_sensor.read_measurement('mid')}")
    print(f"SHT data LO RES  : {sht_sensor.read_measurement('low')}")
    print("")

    print("===========  SPS30  ===========")
    print(f"SPS Firmware version          : {sps_sensor.firmware_version()}")
    print(f"SPS Product type              : {sps_sensor.product_type()}")
    print(f"SPS Serial number             : {sps_sensor.serial_number()}")
    print(f"SPS Status register           : {sps_sensor.read_status_register()}")
    print(f"SPS Set auto cleaning interval: {sps_sensor.write_auto_cleaning_interval_days(SPS_AUTO_CLEANING_DAYS)} sec")
    print(f"SPS Auto cleaning interval    : {sps_sensor.read_auto_cleaning_interval('d')} days")

# Start SPS30 meaasurement
    sps_sensor.start_measurement()
    print(f"SPS data                      : {sps_sensor.read_measurement()}")
    print("===========  LOOP  ===========")

# Load all values in one list/dist and print (or use according to your discretion)
    while True:
        try:
            sensors_values = dict(sht_sensor.read_values(SHT_PRECISION))
            sc.create_json(sensors_values)
            print(sc.post(SC_SHT_PIN))

            sensors_values.update(sps_sensor.read_values())
            sc.create_json(sensors_values)
            print(sc.post(SC_SPS_PIN))

            print(json.dumps(sensors_values, indent=2))
            sleep(PERIOD*60)

        except KeyboardInterrupt:
            sys.exit()

