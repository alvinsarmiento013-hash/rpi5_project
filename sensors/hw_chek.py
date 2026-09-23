import smbus2
import time

I2C_ADDR = 0x49
STATUS_REG = 0x00
WRITE_REG = 0x01
READ_REG = 0x02
HW_VERSION_VIRTUAL_REG = 0x00

bus = smbus2.SMBus(1)

def virtual_read(virtual_reg):
    # wait until ready to write
    while True:
        status = bus.read_byte_data(I2C_ADDR, STATUS_REG)
        if not (status & 0x02):  # TX not busy
            break
    bus.write_byte_data(I2C_ADDR, WRITE_REG, virtual_reg)

    # wait until data ready
    while True:
        status = bus.read_byte_data(I2C_ADDR, STATUS_REG)
        if status & 0x01:  # RX valid
            break
    return bus.read_byte_data(I2C_ADDR, READ_REG)

hw_version = virtual_read(HW_VERSION_VIRTUAL_REG)
print("Hardware version byte:", hex(hw_version))
