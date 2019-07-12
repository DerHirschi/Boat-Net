#!/usr/bin/python
#--------------------------------------
#    ___  ___  _ ____
#   / _ \/ _ \(_) __/__  __ __
#  / , _/ ___/ /\ \/ _ \/ // /
# /_/|_/_/  /_/___/ .__/\_, /
#                /_/   /___/
#
#           bme280.py
#  Read data from a digital pressure sensor.
#
#  Official datasheet available from :
#  https://www.bosch-sensortec.com/bst/products/all_products/bme280
#
# Author : Matt Hawkins
# Date   : 21/01/2018
#
# https://www.raspberrypi-spy.co.uk/
#
#--------------------------------------
import smbus
import time
from gps import *
import os
from ctypes import c_short

import matplotlib as mpl
if not os.environ.get('DISPLAY'):     # Get an Error from python.tk.. Solution from:
    mpl.use('Agg')                    # https://forum.ubuntuusers.de/topic/python3-matplotlib-pyplot-funktioniert-nicht/
import matplotlib.pyplot as plt
import mpld3
import numpy as np


DEVICE = 0x76 # Default device I2C address


bus = smbus.SMBus(1) # Rev 2 Pi, Pi 2 & Pi 3 uses bus 1
                     # Rev 1 Pi uses bus 0


def getShort(data, index):
    # return two bytes from data as a signed 16-bit value
    return c_short((data[index+1] << 8) + data[index]).value


def getUShort(data, index):
    # return two bytes from data as an unsigned 16-bit value
    return (data[index+1] << 8) + data[index]


def getChar(data,index):
    # return one byte from data as a signed char
    result = data[index]
    if result > 127:
        result -= 256
    return result


def getUChar(data,index):
    # return one byte from data as an unsigned char
    result =  data[index] & 0xFF
    return result


def readBME280ID(addr=DEVICE):
    # Chip ID Register Address
    REG_ID     = 0xD0
    (chip_id, chip_version) = bus.read_i2c_block_data(addr, REG_ID, 2)
    return (chip_id, chip_version)


def readBME280All(addr=DEVICE):
# Register Addresses
    REG_DATA = 0xF7
    REG_CONTROL = 0xF4
    REG_CONFIG  = 0xF5

    REG_CONTROL_HUM = 0xF2
    REG_HUM_MSB = 0xFD
    REG_HUM_LSB = 0xFE

    # Oversample setting - page 27
    OVERSAMPLE_TEMP = 2
    OVERSAMPLE_PRES = 2
    MODE = 1

    # Oversample setting for humidity register - page 26
    OVERSAMPLE_HUM = 2
    bus.write_byte_data(addr, REG_CONTROL_HUM, OVERSAMPLE_HUM)

    control = OVERSAMPLE_TEMP<<5 | OVERSAMPLE_PRES<<2 | MODE
    bus.write_byte_data(addr, REG_CONTROL, control)

    # Read blocks of calibration data from EEPROM
    # See Page 22 data sheet
    cal1 = bus.read_i2c_block_data(addr, 0x88, 24)
    cal2 = bus.read_i2c_block_data(addr, 0xA1, 1)
    cal3 = bus.read_i2c_block_data(addr, 0xE1, 7)

    # Convert byte data to word values
    dig_T1 = getUShort(cal1, 0)
    dig_T2 = getShort(cal1, 2)
    dig_T3 = getShort(cal1, 4)

    dig_P1 = getUShort(cal1, 6)
    dig_P2 = getShort(cal1, 8)
    dig_P3 = getShort(cal1, 10)
    dig_P4 = getShort(cal1, 12)
    dig_P5 = getShort(cal1, 14)
    dig_P6 = getShort(cal1, 16)
    dig_P7 = getShort(cal1, 18)
    dig_P8 = getShort(cal1, 20)
    dig_P9 = getShort(cal1, 22)

    dig_H1 = getUChar(cal2, 0)
    dig_H2 = getShort(cal3, 0)
    dig_H3 = getUChar(cal3, 2)

    dig_H4 = getChar(cal3, 3)
    dig_H4 = (dig_H4 << 24) >> 20
    dig_H4 = dig_H4 | (getChar(cal3, 4) & 0x0F)

    dig_H5 = getChar(cal3, 5)
    dig_H5 = (dig_H5 << 24) >> 20
    dig_H5 = dig_H5 | (getUChar(cal3, 4) >> 4 & 0x0F)

    dig_H6 = getChar(cal3, 6)

    # Wait in ms (Datasheet Appendix B: Measurement time and current calculation)
    wait_time = 1.25 + (2.3 * OVERSAMPLE_TEMP) + ((2.3 * OVERSAMPLE_PRES) + 0.575) + ((2.3 * OVERSAMPLE_HUM)+0.575)
    time.sleep(wait_time/1000)  # Wait the required time

    # Read temperature/pressure/humidity
    data = bus.read_i2c_block_data(addr, REG_DATA, 8)
    pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
    temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
    hum_raw = (data[6] << 8) | data[7]

    #Refine temperature
    var1 = ((((temp_raw>>3)-(dig_T1<<1)))*(dig_T2)) >> 11
    var2 = (((((temp_raw>>4) - (dig_T1)) * ((temp_raw>>4) - (dig_T1))) >> 12) * (dig_T3)) >> 14
    t_fine = var1+var2
    temperature = float(((t_fine * 5) + 128) >> 8);

    # Refine pressure and adjust for temperature
    var1 = t_fine / 2.0 - 64000.0
    var2 = var1 * var1 * dig_P6 / 32768.0
    var2 = var2 + var1 * dig_P5 * 2.0
    var2 = var2 / 4.0 + dig_P4 * 65536.0
    var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
    var1 = (1.0 + var1 / 32768.0) * dig_P1
    if var1 == 0:
        pressure=0
    else:
        pressure = 1048576.0 - pres_raw
        pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
        var1 = dig_P9 * pressure * pressure / 2147483648.0
        var2 = pressure * dig_P8 / 32768.0
        pressure = pressure + (var1 + var2 + dig_P7) / 16.0

    # Refine humidity
    humidity = t_fine - 76800.0
    humidity = (hum_raw - (dig_H4 * 64.0 + dig_H5 / 16384.0 * humidity)) * (dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * humidity * (1.0 + dig_H3 / 67108864.0 * humidity)))
    humidity = humidity * (1.0 - dig_H1 * humidity / 524288.0)
    if humidity > 100:
        humidity = 100
    elif humidity < 0:
        humidity = 0

    return temperature/100.0, pressure/100.0, humidity


def main():
    # TODO .. a lot ..
    # TODO Cleanup ( Schnellschuss )
    t = np.load("/home/pi/Scripts/bme2web/t.npy")
    t = t.tolist()
    t1 = np.load("/home/pi/Scripts/bme2web/t1.npy")
    t1 = t1.tolist()

    gpsd = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)

    html1 = open('/var/www/html/index.ba', 'r')
    html2 = open('/var/www/html/page3.ba', 'r')
    html3 = open('/var/www/html/page2.ba', 'r')
    cont1 = html1.read()
    cont2 = html2.read()
    cont3 = html3.read()
    html1.close()
    html2.close()
    html3.close()

    x_axs = []
    for i in range(1440):
        x_axs.append(i / 60)

    while True:
        temperature, pressure, humidity = readBME280All()
        t.append(pressure)
        t1[0].append(temperature)
        t1[1].append(humidity)

        fig, axs = plt.subplots(3, 1)
        axs[0].plot(t, color='tab:green')
        axs[0].set_xlabel('Time (m)')
        axs[0].set_ylabel('Pressure')
        axs[0].grid(True)

        axs[1].set_ylabel('Temperature')
        axs[1].grid(True)
        axs[1].plot(t1[0], color="red")
        axs[2].plot(t1[1], color="blue")
        axs[2].grid(True)
        axs[2].set_ylabel('Humidity')
        fig.tight_layout()
        fig.set_size_inches(12, 10)

        mpld3.save_html(fig, '/var/www/html/plot.html')
        plt.close(fig)
        #
        # 24h plots
        #
        if len(t) > 1440:
            fig, axs = plt.subplots()
            fig.set_size_inches(16, 3)
            axs.set_xlabel('Time (h)')
            axs.set_ylabel('Pressure')
            axs.set_ylim(min(t), max(t))
            axs.grid(True)
            axs.set_xlim(0, 24)
            axs.plot(x_axs, t[-1440:], color='tab:green')
            plt.savefig('/var/www/html/assets/images/pressure-24h-1600x300.png')
            plt.close(fig)

            fig, axs = plt.subplots()
            fig.set_size_inches(16, 3)
            axs.set_xlabel('Time (h)')
            axs.set_ylabel('Humidity')
            axs.set_ylim(min(t1[1]), max(t1[1]))
            axs.grid(True)
            axs.set_xlim(0, 24)
            axs.plot(x_axs, t1[1][-1440:], color='tab:blue')
            plt.savefig('/var/www/html/assets/images/humidity-24h-1600x300.png')
            plt.close(fig)

            fig, axs = plt.subplots()
            fig.set_size_inches(16, 3)
            axs.set_xlabel('Time (h)')
            axs.set_ylabel('Temperature')
            axs.set_ylim(min(t1[0]), max(t1[0]))
            axs.grid(True)
            axs.set_xlim(0, 24)
            axs.plot(x_axs, t1[0][-1440:], color='tab:red')
            plt.savefig('/var/www/html/assets/images/temperature-24h-1600x300.png')
            plt.close(fig)

        #print("Temperature : ", temperature, "C")
        #print("Pressure : ", pressure, "hPa")
        #print("Humidity : ", humidity, "%")
        #print("\n")

        in1 = cont1.find("Temperatur:") + 11
        in2 = cont2.find("Temperatur:") + 11
        newcont1 = cont1[:in1] + ' ' + str(temperature) + ' °C' + cont1[in1:]
        newcont2 = cont2[:in2] + ' ' + str(temperature) + ' °C' + cont2[in2:]
        in1 = newcont1.find("Luftfeuchtigkeit:") + 17
        in2 = newcont2.find("Luftfeuchtigkeit:") + 17
        newcont1 = newcont1[:in1] + ' ' + str(round(humidity, 2)) + ' %' + newcont1[in1:]
        newcont2 = newcont2[:in2] + ' ' + str(round(humidity, 2)) + ' %' + newcont2[in2:]
        in1 = newcont1.find("Luftdruck:") + 10
        in2 = newcont2.find("Luftdruck:") + 10
        cpu_temp = str(measure_temp())[:4]
        newcont1 = newcont1[:in1] + ' ' + str(round(pressure, 5)) + ' hPa<br><br>CPU-Temp.: ' + cpu_temp + ' °C<br>CPU-Load: ' + str(os.getloadavg()) + newcont1[in1:]
        newcont2 = newcont2[:in2] + ' ' + str(round(pressure, 5)) + ' hPa' + newcont2[in2:]

        while True:
            report = gpsd.next()  #
            if report['class'] == 'TPV':
                lat = getattr(report, 'lat', 0.0)
                lon = getattr(report, 'lon', 0.0)
                break

        new_string = "https://map.bootsreisen24.de/?lat=" + str(lat) + "&lng=" + str(lon) + "&zoom=13&marker"
        newcont3 = cont3.replace("https://map.bootsreisen24.de/?lat=53.502035981658466&lng=12.606425285339357&zoom=13&marker", new_string)
        newcont3 = newcont3.replace("https://map.bootsreisen24.de/?lat=53.50859456124775&lng=12.632904052734377&zoom=13", new_string)
        new_string = str(lat) + "," + str(lon) + "&zoom=13&maptype=satellite"

        newcont3 = newcont3.replace("place_id:ChIJXdi14yn_q0cRkLpeW0YgIQQ", new_string)

        html1 = open('/var/www/html/index.html', 'w')
        html2 = open('/var/www/html/page3.html', 'w')
        html3 = open('/var/www/html/page2.html', 'w')
        html1.write(newcont1)
        html2.write(newcont2)
        html3.write(newcont3)
        html1.close()
        html2.close()
        html3.close()
        np.save("/home/pi/Scripts/bme2web/t.npy", t)
        np.save("/home/pi/Scripts/bme2web/t1.npy", t1)

        time.sleep(60)


def measure_temp():
    temp = os.popen("vcgencmd measure_temp").readline()
    return (temp.replace("temp=", ""))


if __name__=="__main__":
    main()
