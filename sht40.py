import sys
from time import sleep
from i2c.i2c import I2C

# I2C commands
CMD_RESET = [0x94]
CMD_SERIAL_NUMBER = [0x89]
CMD_MEASURE = {    #resolution
  'hi':  0xFD,
  'mid': 0xF6,
  'low': 0xE0
}
CMD_HEATER = {   #mW_s
  '20_01':  0x15,
  '20_1':   0x1E,
  '110_01': 0x24,
  '110_1':  0x2F,
  '200_01': 0x32,
  '200_1':  0x39
}

# Length of response in bytes
NBYTES_LENGTH = 6

# Packet size including checksum byte [data1, data2, checksum]
PACKET_SIZE  = 3
SIZE_INTEGER = 3

class SHT40:

# Init I2C BUS
    def __init__(self,  bus: int = 1, address: int = 0x44):
        self.i2c = I2C(bus, address)

# I2C commands BEGIN
    def serial_number(self) -> str:
        self.i2c.write(CMD_SERIAL_NUMBER)
        data = self.i2c.read(NBYTES_LENGTH)
        result = ""
        for i in range(0, NBYTES_LENGTH, PACKET_SIZE):
            if self.crc_calc(data[i:i+2]) != data[i+2]:
                return "CRC mismatch"
            result += "".join(map(str, data[i:i+2]))
        return result

    def activate_heater(self, power_period: str = '20_01') -> str:
        self.i2c.write([CMD_HEATER[power_period]])
        data = self.i2c.read(NBYTES_LENGTH)
        for i in range(0, NBYTES_LENGTH, PACKET_SIZE):
            if self.crc_calc(data[i:i+2]) != data[i+2]:
                return "CRC mismatch"
        return data

    def reset(self) -> None:
        self.i2c.write(CMD_RESET)

    def read_measurement(self, res: str = 'hi') -> list:
        self.i2c.write([CMD_MEASURE[res]])
        sleep(0.01)
        data = self.i2c.read(NBYTES_LENGTH)
        for i in range(0, NBYTES_LENGTH, PACKET_SIZE):
            if self.crc_calc(data[i:i+2]) != data[i+2]:
                return "CRC mismatch"
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
# Helper functions END
#
# Main functions
    def values_to_list(self, data: list) -> dict:
        values = ["t", "h"]
        assoc = {
              "t": 0.0,
              "h": 0.0
        }
        for block, (idx) in enumerate(values):
            sensor_data = []
            for i in range(0, SIZE_INTEGER, PACKET_SIZE):
                offset = (block * SIZE_INTEGER) + i
                if self.crc_calc(data[offset:offset+2]) != data[offset+2]:
                    return {}
                sensor_data.extend(data[offset:offset+2])
            if(idx == 't'):
                assoc[idx] = -45 + 175 *(sensor_data[0] << 8 | sensor_data[1])/65535
            if(idx == 'h'):
                assoc[idx] = -6 + 125 *(sensor_data[0] << 8 | sensor_data[1])/65535
        return assoc

    def read_values(self, res: str = 'hi') -> str:
        return self.values_to_list(self.read_measurement(res))
