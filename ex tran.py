import serial
from time import sleep
port = r'/dev/cu.usbserial-1410'
ser = serial.Serial(port, 115200, timeout=0)

while True:
    ser.write('1'.encode())
    sleep(3)