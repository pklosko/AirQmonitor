import sys
from time import sleep
from i2c.i2c import I2C

# I2C commands
CMD_START_MEASUREMENT      = [0x00, 0x10]
CMD_START_MEASUREMENT_IEE  = [0x00, 0x10, 0x03, 0x00]       #IEEE754_float
CMD_START_MEASUREMENT_INT  = [0x00, 0x10, 0x05, 0x00]       #unsigned_16_bit_integer
CMD_STOP_MEASUREMENT       = [0x01, 0x04]
CMD_READ_DATA_READY_FLAG   = [0x02, 0x02]
CMD_READ_MEASURED_VALUES   = [0x03, 0x00]
CMD_SLEEP                  = [0x10, 0x01]
CMD_WAKEUP                 = [0x11, 0x03]
CMD_START_FAN_CLEANING     = [0x56, 0x07]
CMD_AUTO_CLEANING_INTERVAL = [0x80, 0x04]
CMD_PRODUCT_TYPE           = [0xD0, 0x02]
CMD_SERIAL_NUMBER          = [0xD0, 0x33]
CMD_FIRMWARE_VERSION       = [0xD1, 0x00]
CMD_READ_STATUS_REGISTER   = [0xD2, 0x06]
CMD_CLEAR_STATUS_REGISTER  = [0xD2, 0x10]
CMD_RESET                  = [0xD3, 0x04]

# Length of response in bytes
NBYTES_READ_DATA_READY_FLAG = 3
NBYTES_MEASURED_VALUES_FLOAT = 60  # IEEE754 float
NBYTES_MEASURED_VALUES_INTEGER = 30  # unsigned 16 bit integer
NBYTES_AUTO_CLEANING_INTERVAL = 6
NBYTES_PRODUCT_TYPE = 12
NBYTES_SERIAL_NUMBER = 48
NBYTES_FIRMWARE_VERSION = 3
NBYTES_READ_STATUS_REGISTER = 6

# Packet size including checksum byte [data1, data2, checksum]
PACKET_SIZE = 3

# Size of each measurement data packet (PMx) including checksum bytes, in bytes
SIZE_FLOAT = 6  # IEEE754 float
SIZE_INTEGER = 3  # unsigned 16 bit integer


class SPS30:

# Init I2C BUS
    def __init__(self,  bus: int = 1, address: int = 0x69):
        self.cleaning = 0
        self.i2c      = I2C(bus, address)

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
        return str(result)

    def firmware_version(self) -> str:
        self.i2c.write(CMD_FIRMWARE_VERSION)
        data = self.i2c.read(NBYTES_FIRMWARE_VERSION)
        if self.crc_calc(data[:2]) != data[2]:
            return "CRC mismatch"
        return ".".join(map(str, data[:2]))

    def product_type(self) -> str:
        self.i2c.write(CMD_PRODUCT_TYPE)
        data = self.i2c.read(NBYTES_PRODUCT_TYPE)
        result = ""
        for i in range(0, NBYTES_PRODUCT_TYPE, 3):
            if self.crc_calc(data[i:i+2]) != data[i+2]:
                return "CRC mismatch"
            if(data[i:i+2] != [0x00, 0x00]):
                result += "".join(map(chr, data[i:i+2]))
        return str(result)

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
        laser_status = "outofrange" if int(binary[26]) == 1 else "ok"
        fan_status = "0rpm" if int(binary[27]) == 1 else "ok"
        return {
            "speed": speed_status,
            "laser": laser_status,
            "fan": fan_status
        }

    def clear_status_register(self) -> None:
        self.i2c.write(CMD_CLEAR_STATUS_REGISTER)

    def read_data_ready_flag(self) -> bool:
        self.i2c.write(CMD_READ_DATA_READY_FLAG)
        data = self.i2c.read(NBYTES_READ_DATA_READY_FLAG)
        if self.crc_calc(data[:2]) != data[2]:
            return False
        return True if data[1] == 1 else False

    def sleep(self) -> None:
        self.i2c.write(CMD_SLEEP)

    def wakeup(self) -> None:
        self.i2c.write(CMD_WAKEUP)

    def start_fan_cleaning(self) -> None:
        self.cleaning = 1
        self.i2c.write(CMD_START_FAN_CLEANING)
        sleep(12)
        self.cleaning = 0

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

    def write_auto_cleaning_interval_days(self, days: int) -> int:
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
        sleep(0.05)
        return self.read_auto_cleaning_interval()

    def reset(self) -> None:
        self.i2c.write(CMD_RESET)

    def stop_measurement(self) -> None:
        self.i2c.write(CMD_STOP_MEASUREMENT)
        self.i2c.close()

    def start_measurement(self) -> None:
        data = CMD_START_MEASUREMENT_IEE
        data.append(self.crc_calc(data[2:4]))
        self.i2c.write(data)
        sleep(0.05)

    def read_measurement(self) -> list:
        if not self.read_data_ready_flag():
            sleep(1)
        self.i2c.write(CMD_READ_MEASURED_VALUES)
        data = self.i2c.read(NBYTES_MEASURED_VALUES_FLOAT)
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

    def ieee754_number_conversion(self, data: int) -> float:
        binary = "{:032b}".format(data)
        sign = int(binary[0:1])
        exp = int(binary[1:9], 2) - 127
        exp = 0 if exp < 0 else exp
        mantissa = binary[9:]
        real = int(('1' + mantissa[:exp]), 2)
        decimal = mantissa[exp:]
        dec = 0.0
        for i in range(len(decimal)):
            dec += int(decimal[i]) / (2**(i+1))
        return round((((-1)**(sign) * real) + dec), 3)

    def is_cleaning(self) -> int:
        return self.cleaning

# Helper functions END
#
# Main functions
    def values_to_list(self, data: list) -> dict:
        values = ["pm1", "pm2", "pm4", "pm10", "nc0", "nc1", "nc2", "nc4", "nc10", "tps"]
        assoc = {
              "pm1":  0.0,
              "pm2":  0.0,
              "pm4":  0.0,
              "pm10": 0.0,
              "nc0":  0.0,
              "nc1":  0.0,
              "nc2":  0.0,
              "nc4":  0.0,
              "nc10": 0.0,
              "tps":  0.0
        }
        for block, (idx) in enumerate(values):
            sensor_data = []
            for i in range(0, SIZE_FLOAT, PACKET_SIZE):
                offset = (block * SIZE_FLOAT) + i
                if self.crc_calc(data[offset:offset+2]) != data[offset+2]:
                    return {}
                sensor_data.extend(data[offset:offset+2])
            assoc[idx] = self.ieee754_number_conversion(
                sensor_data[0] << 24 | sensor_data[1] << 16 | sensor_data[2] << 8 | sensor_data[3])
        return assoc

    def read_values(self) -> dict:
        return self.values_to_list(self.read_measurement())
