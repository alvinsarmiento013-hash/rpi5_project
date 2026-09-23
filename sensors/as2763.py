import board
import busio
from adafruit_as726x import AS726x_I2C

i2c = busio.I2C(board.SCL, board.SDA)
sensor = AS726x_I2C(i2c)

print("Sensor connected!")
print("Temperature:", sensor.temperature)

# Take a reading
sensor.driver_led = True   # turn on the illumination LED
import time
time.sleep(0.5)

print("Violet:", sensor.violet)
print("Blue:", sensor.blue)
print("Green:", sensor.green)
print("Yellow:", sensor.yellow)
print("Orange:", sensor.orange)
print("Red:", sensor.red)

sensor.driver_led = False
