# Air Quality Monitor 

## Introduction

Python-based drivers for 
  - [Sensirion SPS30](https://sensirion.com/products/catalog/SPS30/) particulate matter sensor.
  - [Sensirion SHT40](https://sensirion.com/products/catalog/SHT40/) .1.8% / max. .3.5% Digital humidity and temperature sensor.
  - [BOSCH BMP280](https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/bmp280/) absolute barometric pressure sensor

Tested on Raspberry Pi Zero/Zero W2.

### Wiring

#### SPS30 Sensor

```none
                                 Pin 1   Pin 5
                                   |       |
                                   V       V
.------------------------------------------------.
|                                .-----------.   |
|                                | x x x x x |   |
|                                '-----------'   |
|     []          []          []          []     |
'------------------------------------------------'
```

| Pin | Description                                       | UART | I2C |
| :-: | :------------------------------------------------ | ---- | --- |
|  1  | Supply voltage 5V                                 | VDD  | VDD |
|  2  | UART receiving pin/ I2C serial data input/ output | RX   | SDA |
|  3  | UART transmitting pin/ I2C serial clock input     | TX   | SCL |
|  4  | Interface select (UART: floating (NC) /I2C: GND)  | NC   | GND |
|  5  | Ground                                            | GND  | GND |

#### I2C Interface

```none
  Sensor Pins                                 Raspberry Pi Pins 
                                              [default, see below for alternative i2c buses]
.-------.-----.                             .----------.---------.
| Pin 1 | VDD |-----------------------------|    5V    | Pin 2/4 |
| Pin 2 | SDA |-----------------------------| I2C1 SDA |  Pin 3  |
| Pin 3 | SCL |-----------------------------| I2C1 SCL |  Pin 5  |
| Pin 4 | GND |-----.                       |          |         |
| Pin 5 | GND |-----'-----------------------|   GND    | Pin 6/9 |
'-------'-----'                             '----------'---------'
```

#### Multiple I2C Interfaces @ RPi

- [Raspberry PI Multiple I2C Devices](https://www.instructables.com/Raspberry-PI-Multiple-I2c-Devices/)
- [Changing the baud rate of additional I2C busses](https://tlfong01.blog/2020/09/24/changing-the-baud-rate-of-additional-i2c-busses/)

```none

  sudo nano /boot/config.txt
  
  dtoverlay=i2c-gpio,bus=5,i2c_gpio_delay_us=20,i2c_gpio_sda=5,i2c_gpio_scl=6
  dtoverlay=i2c-gpio,bus=4,i2c_gpio_delay_us=20,i2c_gpio_sda=23,i2c_gpio_scl=24
  dtoverlay=i2c-gpio,bus=3,i2c_gpio_delay_us=20,i2c_gpio_sda=17,i2c_gpio_scl=27

```

### Example usage

#### See example.py
 
Default parameters of `SPS30` class

| Parameter | Value | Description             |
| --------- | ----- | ----------------------- |
| bus       | 1     | I2C bus of Raspberry Pi |
| address   | 0x69  | Default I2C address     |


Default parameters of `SHT40` class

| Parameter | Value | Description             |
| --------- | ----- | ----------------------- |
| bus       | 1     | I2C bus of Raspberry Pi |
| address   | 0x44  | Default I2C address     |


Default parameters of `BMP280` class

| Parameter      | Value  | Description              |
| ---------------| ------ | ------------------------ |
| bus            | 1      | I2C bus of Raspberry Pi  |
| address        | 0x77   | Default I2C address      |
| oversampling T | 1x     | temperature oversampling |
| oversampling p | 1x     | pressure oversampling    |
| standby time   | 1s     | stand-by time            |
| IIR filter     | off    | IIR filter               |
| Mode           | forced | mode                     |

#### Output data format

```json
{
  "t": 22.02258335240711,
  "t1": 22.546321267577, 
  "h": 41.55664911879148,
  "p": 100142.342398298,
  "pm1": 1.285,
  "pm2": 5.262,
  "pm4": 9.045,
  "pm10": 10.969,
  "nc0": 1.0,
  "nc1": 1.0,
  "nc2": 4.473,
  "nc4": 5.034,
  "nc10": 5.11,
  "tps": 1.63
}
``` 

### Dependencies

None

### To-Do

- daemonize
- sleep SPS30 in wait cycle of loop & waiting for relevant data. See [Low-Power Operation](https://sensirion.com/media/documents/188A2C3C/6166F165/Sensirion_Particulate_Matter_AppNotes_SPS30_Low_Power_Operation_D1.pdf)

#### SPS30 code based on [Sensirion SPS30 code by @dvsu](https://github.com/dvsu/sps30)



