import sys
from time import sleep
from i2c.i2c import I2C

# I2C commands
CMD_CALIB       = [0x88]
CMD_DEVICE_ID   = [0xD0]
CMD_RESET       = [0xE0]
CMD_STATUS      = [0xF3]
CMD_MEAS        = [0xF4]
CMD_CONFIG      = [0xF5]
CMD_PRESSURE    = [0xF7]
CMD_TEMPERATURE = [0xFA]

# Settings registers
# Oversampling
OS_P_NONE = 0b000
OS_P_x1   = 0b001 #default
OS_P_x2   = 0b010
OS_P_x4   = 0b011
OS_P_x8   = 0b100
OS_P_x16  = 0b101

OS_T_NONE = 0b000
OS_T_x1   = 0b001 #default
OS_T_x2   = 0b010
OS_T_x4   = 0b011
OS_T_x8   = 0b100
OS_T_x16  = 0b101

# Standby time [ms]
T_SB_0p5  = 0b000
T_SB_62p5 = 0b001
T_SB_125  = 0b010
T_SB_250  = 0b011
T_SB_500  = 0b100
T_SB_1000 = 0b101
T_SB_2000 = 0b110
T_SB_4000 = 0b111 #default

# IIR filetr
IIR_OFF = 0b000 #default
IIR_x2  = 0b001
IIR_x4  = 0b010
IIR_x8  = 0b011
IIR_x16 = 0b100

# Mode
MODE_SLEEP  = 0b00
MODE_FORCED = 0b01
MODE_NORMAL = 0b11 #defsult

# Length of response in bytes
NBYTES_CALIB   = 24
NBYTES_TEMP_P  = 3
NBYTES_LENGTH  = 1

# Packet size
CALIB_PACKET_SIZE  = 2

class BMP280:

# Init I2C BUS
    def __init__(self,  bus: int = 1, address: int = 0x77,
                        os_p: int = OS_P_x1,
                        os_t: int = OS_T_x1,
                        t_sb: int = T_SB_1000,
                        iir:  int = IIR_OFF,
                        mode: int = MODE_FORCED):
        self.ctrl_meas_reg = 0
        self.config_reg    = 0
        self.t_fine        = 0
        self.calib_data    = {
            'T1': 0,
            'T2': 0,
            'T3': 0,
            'P1': 0,
            'P2': 0,
            'P3': 0,
            'P4': 0,
            'P5': 0,
            'P6': 0,
            'P7': 0,
            'P8': 0,
            'P9': 0
        }
        self.i2c  = I2C(bus, address)
        self.type = "BMP280"
        self.sn   = self.device_id()

# I2C commands BEGIN
    def device_id(self) -> int:
        self.i2c.write(CMD_DEVICE_ID)
        data = self.i2c.read(NBYTES_LENGTH)
        if (data[0] != 0x58):
            return False
        return data

    def reset(self) -> None:
        self.i2c.write(CMD_RESET)

    def set_meas_reg(self, os_p: int = OS_P_x1,
                           os_t: int = OS_T_x1,
                           mode: int = MODE_FORCED) -> None:
        self.ctrl_meas_reg = mode + (os_p << 2) + (os_t << 5)
        cmd = CMD_MEAS
        cmd.extend([self.ctrl_meas_reg])
        self.i2c.write(cmd)

    def meas_reg(self) -> int:
        self.i2c.write(CMD_MEAS)
        return self.i2c.read(NBYTES_LENGTH)

    def set_ctrl_reg(self, iir: int = IIR_OFF,
                           t_sb: int = T_SB_1000) -> None:
        self.config_reg = 0b000 + (iir << 2) + (t_sb << 5)
        cmd = CMD_CONFIG
        cmd.extend([self.config_reg])
        self.i2c.write(cmd)

    def ctrl_reg(self) -> int:
        self.i2c.write(CMD_CONFIG)
        return self.i2c.read(NBYTES_LENGTH)

    def calib_reg(self) -> list:
        self.i2c.write(CMD_CALIB)
        return self.i2c.read(NBYTES_CALIB)

    def temp_press_reg(self, cmd: int = CMD_TEMPERATURE) -> int:
        self.i2c.write(cmd)
        data = self.i2c.read(NBYTES_TEMP_P)
        return (data[0] << 16 | data[1] << 8 | data[2]) >> 4
# I2C commands END
#
# Helper functions BEGIN
    def to_signed(self, c_data: int) -> int:
        if(c_data > 0x7FFF):
            return c_data - 0x10000
        else:
            return c_data

    def read_calib_data(self, data: list) -> dict:
        i = 0
        for calib in self.calib_data:
            offset = (i * CALIB_PACKET_SIZE)
            c_data = (data[offset+1] << 8 | data[offset])
            if(i == 0 or i == 3):
                self.calib_data[calib] = c_data
            else:
                self.calib_data[calib] = self.to_signed(c_data)
            i = i + 1
        return self.calib_data

    def calc_t(self, adc_t: int) -> float:
        var1 = ((adc_t / 16384.0) - (self.calib_data['T1'] / 1024.0)) * self.calib_data['T2']
        var2 = ((adc_t / 131072.0) - (self.calib_data['T1'] / 8192.0)) * ((adc_t / 131072.0) - (self.calib_data['T2'] / 8192.0)) * self.calib_data['T3']
        self.t_fine = var1 + var2
        return (var1+var2) / 5120.0

    def calc_p(self, adc_p: int) -> float:
        var1 = (self.t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self.calib_data['P6'] / 32768.0
        var2 = var2 + var1 * self.calib_data['P5'] * 2.0
        var2 = (var2 / 4.0) + (self.calib_data['P4'] * 65536.0)
        var1 = (self.calib_data['P3'] * var1 * var1 / 524288.0 + (self.calib_data['P2'] * var1)) / 524288.0
        var1 = (1.0 + (var1 / 32768.0)) * self.calib_data['P1']
        if(var1 == 0):
            return 0
        p = 1048576.0 - adc_p
        p = (p - (var2 / 4096.0)) * 6250.0 / var1
        var1 = self.calib_data['P9'] * p * p / 2147483648.0
        var2 = p * self.calib_data['P8'] / 32768.0
        p += (var1 + var2 + self.calib_data['P7']) / 16.0
        return p

# Helper functions END
#
# Main functions
    def temperature(self) -> float:
        return self.calc_t(self.temp_press_reg())

    def pressure(self) -> float:
        self.calc_t(self.temp_press_reg())
        return self.calc_p(self.temp_press_reg(CMD_PRESSURE))

    def values_to_list(self) -> dict:
        self.set_meas_reg()
        sleep(0.01)
        assoc = {
              "t1": self.temperature(),
              "p": self.pressure()
        }
        return assoc

    def read_values(self) -> str:
        return self.values_to_list()
