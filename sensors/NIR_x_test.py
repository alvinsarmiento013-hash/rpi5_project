import board
import busio
from adafruit_as726x import AS726x_I2C

i2c = busio.I2C(board.SCL, board.SDA)
sensor = AS726x_I2C(i2c)

print("Hardware version:", hex(sensor.hw_version))
