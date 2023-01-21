import sys
from time import sleep
from datetime import datetime
from i2c.i2c import I2C

# I2C commands
CMD_START_MEASUREMENT      = [0x00, 0x21]
CMD_START_MEASUREMENT_RHT  = [0x00, 0x37]
CMD_STOP_MEASUREMENT       = [0x01, 0x04]
CMD_READ_DATA_READY_FLAG   = [0x02, 0x02]
CMD_READ_MEASURED_VALUES   = [0x03, 0xc4]
CMD_START_FAN_CLEANING     = [0x56, 0x07]
CMD_AUTO_CLEANING_INTERVAL = [0x80, 0x04]
CMD_PRODUCT_NAME           = [0xD0, 0x14]
CMD_SERIAL_NUMBER          = [0xD0, 0x33]
CMD_FIRMWARE_VERSION       = [0xD1, 0x00]
CMD_READ_STATUS_REGISTER   = [0xD2, 0x06]
CMD_CLEAR_STATUS_REGISTER  = [0xD2, 0x10]
CMD_RESET                  = [0xD3, 0x04]

CMD_THERMO_COMPENS_PARAM   = [0x60, 0xb2]
CMD_WARM_START_PARAM       = [0x60, 0xc6]
CMD_VOC_TUNNING_PARAM      = [0x60, 0xd0]
CMD_NOX_TUNNING_PARAM      = [0x60, 0xe1] #SEN55 only
CMD_RHT_ACC_MODE           = [0x60, 0xf7]
CMD_VOC_ALGO_STATE         = [0x61, 0x81]

DEFAULT_VOC_TUNNING_PARAM  = [0x00, 0x64, 0xfe, 0x00, 0x0c, 0xfc, 0x00, 0x0c, 0xfc, 0x00, 0xb4, 0xfa, 0x00, 0x32, 0x26, 0x00, 0xe6, 0xe6]

# SEN55 Only
DEFAULT_NOX_TUNNING_PARAM  = [0x00, 0x01, 0xb0, 0x00, 0x0c, 0xfc, 0x00, 0x0c, 0xfc, 0x02, 0xd0, 0x5c, 0x00, 0x32, 0x26, 0x00, 0xe6, 0xe6]

# Length of response in bytes
NBYTES_READ_DATA_READY_FLAG   = 3
NBYTES_MEASURED_VALUES        = 24
NBYTES_AUTO_CLEANING_INTERVAL = 6
NBYTES_PRODUCT_NAME           = 48
NBYTES_SERIAL_NUMBER          = 48
NBYTES_FIRMWARE_VERSION       = 3
NBYTES_READ_STATUS_REGISTER   = 6
NBYTES_RHT_ACC_MODE           = 3
NBYTES_VOC_ALGO_STATE         = 12
NBYTES_VOC_NOX_TUNNING_PARAM  = 18
NBYTES_WARM_START_PARAM       = 3
NBYTES_THERMO_COMPENS_PARAM   = 9


# Packet size including checksum byte [data1, data2, checksum]
PACKET_SIZE = 3

# Size of each measurement data packet (PMx) including checksum bytes, in bytes
SIZE_INTEGER = 3  # unsigned 16 bit integer

# Error value
SEN_DATA_ERR = [0x80,0x7F]  #-127.0
#[0xBF,0x80,0x00,0x00]  #-1.0

class SEN5x:

# Init I2C BUS
    def __init__(self,  bus: int = 1, address: int = 0x69):
        self.cleaning    = 0
        self.cleaning_ts = 0
        self.i2c         = I2C(bus, address)
        self.type        = self.product_name()
        self.sn          = self.serial_number()
        self.fw          = self.firmware_version()


# I2C commands BEGIN
    def serial_number(self) -> str:
        self.i2c.write(CMD_SERIAL_NUMBER)
        data = self.i2c.read(NBYTES_SERIAL_NUMBER)
        result = ""
        for i in range(0, NBYTES_SERIAL_NUMBER, PACKET_SIZE):
            if self.crc_calc(data[i:i+2]) != data[i+2]:
                return "CRC mismatch"
            if(data[i:i+2] != [0x00, 0x00]):
                result += "".join(map(chr, data[i:i+2]))
        return str(result.rstrip('\x00'))

    def firmware_version(self) -> str:
        self.i2c.write(CMD_FIRMWARE_VERSION)
        data = self.i2c.read(NBYTES_FIRMWARE_VERSION)
        if self.crc_calc(data[:2]) != data[2]:
            return "CRC mismatch"
        return ".".join(map(str, data[:2]))

    def product_name(self) -> str:
        self.i2c.write(CMD_PRODUCT_NAME)
        data = self.i2c.read(NBYTES_PRODUCT_NAME)
        result = ""
        for i in range(0, NBYTES_PRODUCT_NAME, 3):
            if self.crc_calc(data[i:i+2]) != data[i+2]:
                return "CRC mismatch"
            if(data[i:i+2] != [0x00, 0x00]):
                result += "".join(map(chr, data[i:i+2]))
        return str(result.rstrip('\x00'))

    def read_status_register(self) -> dict:
        self.i2c.write(CMD_READ_STATUS_REGISTER)
        data = self.i2c.read(NBYTES_READ_STATUS_REGISTER)
        status = []
        for i in range(0, NBYTES_READ_STATUS_REGISTER, PACKET_SIZE):
            if self.crc_calc(data[i:i+2]) != data[i+2]:
                return "CRC mismatch"
            status.extend(data[i:i+2])
        binary = '{:032b}'.format(
            status[0] << 24 | status[1] << 16 | status[2] << 8 | status[3])

        speed_status = "high/low" if int(binary[10]) == 1 else "ok"
        clean_status = "cleaning" if int(binary[12]) == 1 else "normal"
        gas_status   = "error" if int(binary[24]) == 1 else "ok"
        rht_status   = "error" if int(binary[25]) == 1 else "ok"
        laser_status = "outofrange" if int(binary[26]) == 1 else "ok"
        fan_status   = "0rpm" if int(binary[27]) == 1 else "ok"
        sen_status   = (int(binary[10]) | int(binary[12]) | int(binary[24]) | int(binary[25]) | int(binary[26]) | int(binary[27]))

        return {
            "speed": speed_status,
            "clean": clean_status,
            "laser": laser_status,
            "fan":   fan_status,
            "rht":   rht_status,
            "gas":   gas_status,
            "status":sen_status
        }

    def clear_status_register(self) -> None:
        self.i2c.write(CMD_CLEAR_STATUS_REGISTER)

    def read_data_ready_flag(self) -> bool:
        self.i2c.write(CMD_READ_DATA_READY_FLAG)
        data = self.i2c.read(NBYTES_READ_DATA_READY_FLAG)
        if self.crc_calc(data[0:2]) != data[2]:
            return False
        return True if data[1] == 1 else False

    def read_rht_acceleration_mode(self) -> int:
        self.i2c.write(CMD_READ_RHT_ACC_MODE)
        data = self.i2c.read(NBYTES_READ_DATA_READY_FLAG)
        if self.crc_calc(data[0:2]) != data[2]:
            return -1
        return (data[0] << 8 | data[1])

    def read_warm_start_param(self, writeCMD : int = 1) -> int:
        if writeCMD == 1:
            self.i2c.write(CMD_WARM_START_PARAM)
        data = self.i2c.read(NBYTES_WARM_START_PARAM)
        if self.crc_calc(data[0:2]) != data[2]:
            return -1
        return (data[0] << 8 | data[1])

    def write_warm_start_param(self, param:int) -> None:
        data = CMD_WARM_START_PARAM
        data.append((param & 0xff00) >> 8)
        data.append(param & 0x00ff)
        data.append(self.crc_calc(data[2:4]))
        print(data) 
        self.i2c.write(data)

    def start_fan_cleaning(self) -> None:
        self.cleaning = 1
        self.i2c.write(CMD_START_FAN_CLEANING)
        sleep(12)
        self.cleaning = 0
        self.cleaning_ts = int(datetime.now().timestamp())

    def read_auto_cleaning_interval(self, unit: str = 's') -> int:
        dividier = {
            'd' : 86400,
            'm' : 3600,
            'h' : 60,
            's' : 1
        }
        self.i2c.write(CMD_AUTO_CLEANING_INTERVAL)
        data = self.i2c.read(NBYTES_AUTO_CLEANING_INTERVAL)
        interval = []
        for i in range(0, NBYTES_AUTO_CLEANING_INTERVAL, 3):
            if self.crc_calc(data[i:i+2]) != data[i+2]:
                return "CRC mismatch"
            interval.extend(data[i:i+2])
        ret = (interval[0] << 24 | interval[1] << 16 | interval[2] << 8 | interval[3])
        return ret / dividier[unit]

    def write_auto_cleaning_interval_days(self, days: int) -> None:
        seconds = days * 86400
        interval = []
        interval.append((seconds & 0xff000000) >> 24)
        interval.append((seconds & 0x00ff0000) >> 16)
        interval.append((seconds & 0x0000ff00) >> 8)
        interval.append(seconds & 0x000000ff)
        data = CMD_AUTO_CLEANING_INTERVAL
        data.extend([interval[0], interval[1]])
        data.append(self.crc_calc(data[2:4]))
        data.extend([interval[2], interval[3]])
        data.append(self.crc_calc(data[5:7]))
        self.i2c.write(data)

    def read_thermo_compensation_param(self) -> list:
        self.i2c.write(CMD_THERMO_COMPENS_PARAM)
        data = self.i2c.read(NBYTES_THERMO_COMPENS_PARAM)
        return data

    def read_voc_tunning_param(self) -> list:
        self.i2c.write(CMD_VOC_TUNNING_PARAM)
        data = self.i2c.read(NBYTES_VOC_NOX_TUNNING_PARAM)
        return data

    def write_voc_tunning_param(self, param:list) -> None:
        data = CMD_VOC_TUNNING_PARAM
        if param[0] == 255:
            param = DEFAULT_VOC_TUNNING_PARAM
        for i in range(0, NBYTES_VOC_NOX_TUNNING_PARAM, PACKET_SIZE):
            if self.crc_calc(param[i:i+2]) != param[i+2]:
                return "CRC mismatch"
        data.extend(param)
        print(data)
        self.i2c.write(data)

    def read_nox_tunning_param(self) -> list:
        self.i2c.write(CMD_NOX_TUNNING_PARAM)
        data = self.i2c.read(NBYTES_VOC_NOX_TUNNING_PARAM)
        return data

    def write_nox_tunning_param(self, param:list) -> None:
        data = CMD_NOX_TUNNING_PARAM
        if param[0] == 255:
            param = DEFAULT_VOC_TUNNING_PARAM
        for i in range(0, NBYTES_VOC_NOX_TUNNING_PARAM, PACKET_SIZE):
            if self.crc_calc(param[i:i+2]) != param[i+2]:
                return "CRC mismatch"
        data.extend(param)
        print(data)
        self.i2c.write(data)

    def read_voc_algo_state(self) -> list:
        self.i2c.write(CMD_VOC_ALGO_STATE)
        data = self.i2c.read(NBYTES_VOC_ALGO_STATE)
        return data

    def write_voc_algo_state(self, param:list) -> None:
        data = CMD_VOC_ALGO_STATE
        for i in range(0, NBYTES_VOC_ALGO_STATE, PACKET_SIZE):
            if self.crc_calc(param[i:i+2]) != param[i+2]:
                return "CRC mismatch"
        data.extend(param)
        print(data)
        self.i2c.write(data)

    def reset(self) -> None:
        self.i2c.write(CMD_RESET)

    def stop_measurement_and_close(self) -> None:
        self.i2c.write(CMD_STOP_MEASUREMENT)
#        self.save_to_file(self.type + '-' + self.sn + '-VOCalgo.bin', self.read_voc_algo_state())
        self.i2c.close()

    def stop_measurement(self) -> None:
        self.i2c.write(CMD_STOP_MEASUREMENT)
        sleep(0.05)

    def start_measurement(self) -> None:
        self.i2c.write(CMD_START_MEASUREMENT)
        sleep(0.05)

    def read_measurement(self) -> list:
        if not self.read_data_ready_flag():
            sleep(1)
        self.i2c.write(CMD_READ_MEASURED_VALUES)
        data = self.i2c.read(NBYTES_MEASURED_VALUES)
        return data

# I2C commands END
#
# Helper functions BEGIN
    def crc_calc(self, data: list) -> int:
        crc = 0xFF
        for i in range(2):
            crc ^= data[i]
            for _ in range(8, 0, -1):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return (crc & 0x0000FF)

    def int16_number_conversion(self, data: int) -> int:
        return data if (data < 0x8000) else data - 0xFFFF

    def is_cleaning(self) -> int:
        return self.cleaning

    def to_file(self, filename: str, data: list, binary: int = 1) -> str:
        if binary == 1:
            bin_data = bytearray(data)
            with open(filename, 'wb') as bin_file:
               bin_file.write(bin_data)
        return filename

    def from_file(self, filename: str, binary: int = 1) -> list:
        bin_file = open(filename, 'rb')
        return list(bin_file.read())

# Helper functions END
#
# Main functions
    def values_to_list(self, data: list, sensorType: str = "SEN55") -> dict:
        values = ["pm1", "pm2", "pm4", "pm10", "h", "t", "voc"]
        scale = {
              "pm1":  10,
              "pm2":  10,
              "pm4":  10,
              "pm10": 10,
              "h":    100,
              "t":    200,
              "voc":  10,
              "nox":  10
        }
        assoc = {
              "t":    0.0,
              "h":    0.0,
              "pm1":  0.0,
              "pm2":  0.0,
              "pm4":  0.0,
              "pm10": 0.0,
              "voc":  0.0
        }
        if sensorType == "SEN55":
          values.append("nox")
          assoc.update({"nox":0.0})

        for block, (idx) in enumerate(values):
            sensor_data = []
            for i in range(0, SIZE_INTEGER, PACKET_SIZE):
                offset = (block * SIZE_INTEGER) + i
                if self.crc_calc(data[offset:offset+2]) != data[offset+2]:
                    sensor_data.extend(SEN_DATA_ERR)
                else:
                    sensor_data.extend(data[offset:offset+2])

            if block > 3:
                assoc[idx] = self.int16_number_conversion(sensor_data[0] << 8 | sensor_data[1]) / scale[idx]
            else:
                assoc[idx] = (sensor_data[0] << 8 | sensor_data[1]) / scale[idx]
        return assoc

    def status_to_str(self, sen_status_register: dict) -> str:
        sen_info = ""
        if(sen_status_register['status'] != 0):
            for key in sen_status_register:
                sen_info = sen_info + "/" + key + "-" + sen_status_register[key]
            sen_info = sen_info + "]"
        else:
            sen_info = "SEN-OK]"
        return sen_info

    def read_values(self) -> dict:
        return self.values_to_list(self.read_measurement(), self.type)

    def read_status(self) -> dict:
        sen_status_register = self.read_status_register()
        return {
            "text": self.status_to_str(sen_status_register),
            "stat": str(sen_status_register['status']) + "0000000"
        }
