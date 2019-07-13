[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
# Boat-Net (Python3)
--
WEB-GUI based system for camping or boat trips, runable on raspberry pi 3, includes:
#
#### LTE Antenna Rotator:
- Rotator is scanning for best net ( 3G / 4G ) and align to strongest signal
- Scan cycles and methode dependent on changing GPS position and signal strength

  Scan methodes Ideas (need a solution: my servo for the rotator is pretty noisy):
  - activ fast scan (pretty noisy)
  - activ slow scan (not so noisy)
  - passiv scan (without rotating servo.. just let the boat rotate in the wind if set anchor)

  HW-Setup:
  - LTE-Modem: Huawei e3372
  - Antenna rotor controller: Arduino Mega 2560 or Arduino Nano
  - Gyro / Compass sensor for Arduino: GY-91 MPU9250 BMP280 10DOF 
  - https://www.instructables.com/id/Tilt-Compensated-Compass/
#
#### Free WIFI Scanner:
- Scanning permanently for free WIFI and test ping 8.8.8.8 if usable
- #### Using VPN
#
#### Weather Information:
- plot data from weather sensor on raspberry pi to web page

  HW-Setup:
  - Weather sensor: BME280 on Raspberry pi
  - https://www.raspberrypi-spy.co.uk/2016/07/using-bme280-i2c-temperature-pressure-sensor-in-python/


#
#### GPS Information:
- change GPS cordinates for Maps an Links on web page

  HW-Setup:
  - GPS - Stick: Diymall Vk-172 vk 172 Gmouse G-Maus Usb
#
<br/><br/>

### Prerequisites:
- huawei-lte-api
- pySerial
- matplotlib
- shutil

for bme2800.py additional:
- mpld3
- smbus
- gps

<br/><br/>
## Sources:
<br/>

### Web Site was made with Mobirise Website Builder.
##### https://mobirise.com
#

### Arduino Script based on Code by LINGIB:
##### Source: https://www.instructables.com/id/Tilt-Compensated-Compass/
#

### bme280.py Script  based on Code by Matt Hawkins:
##### Code: https://bitbucket.org/MattHawkinsUK/rpispy-misc/raw/master/python/bme280.py  
##### Source:  https://www.raspberrypi-spy.co.uk/2016/07/using-bme280-i2c-temperature-pressure-sensor-in-python/
#

### Python Huawei LTE API
##### https://pypi.org/project/huawei-lte-api/
<br/>

#
### Status:
All of this are under development.
Some parts, like wifi/main.py 
or web_gui/bme280.py, are ready to useable as standalone.
</br>

<br/><br/><br/>
#
#
### so..
# A lot to do !!!
Where is the piano, I carry the notes...



