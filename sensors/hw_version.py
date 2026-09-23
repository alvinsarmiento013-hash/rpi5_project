import smbus2
import time

I2C_ADDR = 0x49
STATUS_REG = 0x00
WRITE_REG = 0x01
READ_REG = 0x02

bus = smbus2.SMBus(1)

def virtual_read(virtual_reg):
    while True:
        status = bus.read_byte_data(I2C_ADDR, STATUS_REG)
        if not (status & 0x02):
            break
    bus.write_byte_data(I2C_ADDR, WRITE_REG, virtual_reg)
    while True:
        status = bus.read_byte_data(I2C_ADDR, STATUS_REG)
        if status & 0x01:
            break
    return bus.read_byte_data(I2C_ADDR, READ_REG)

device_type = virtual_read(0x00)
hw_version = virtual_read(0x01)
print("Device Type:", hex(device_type))
print("HW Version:", hex(hw_version))
