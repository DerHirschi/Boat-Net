# Boat-Net (Python3)
--
WEB-GUI based system for camping or boat trips, runable on raspberry pi 3, includes:

####LTE Antenna Rotator:
- Rotator is scanning for best net ( 3G / 4G ) and align to strongest signal
- Scan cycles and methode dependent on changing GPS position and signal strength

  Scan methodes Ideas (need a solution: my servo for the rotator is pretty noisy):
  - activ fast scan (pretty noisy)
  - activ slow scan (not so noisy)
  - passiv scan (without rotating servo.. just let the boat rotate in the wind if set anchor)

  Setup:
  - LTE-Modem: Huawei e3372
  - Antenna rotor controller: Arduino Mega 2560 or Arduino Nano
  - Gyro / Compass sensor for Arduino: GY-91 MPU9250 BMP280 10DOF 

####Free WIFI Scanner:
- Scanning permanently for free WIFI and test with ping 8.8.8.8 if usable
- #### Using VPN

####Weather Information:
- plot data from weather sensor on raspberry pi to web page

  Setup:
  - Weather sensor: BME280



####GPS Information:
- change GPS cordinates for Maps an Links on web page

  Setup:
  - GPS - Stick: Diymall Vk-172 vk 172 Gmouse G-Maus Usb


###Prerequisites  
- huawei-lte-api
- pySerial
- matplotlib
- shutil

for bme2800.py additional:
- mpld3
- smbus
- gps
