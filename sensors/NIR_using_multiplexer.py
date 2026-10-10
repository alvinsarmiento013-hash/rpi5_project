#!/usr/bin/env python3
"""
nir_two_sensor_test.py - 2x AS7263 through a PCA9548A (Raspberry Pi 5)

Asks for a test note -> 5 s countdown -> logs both sensors for 10 s -> saves one CSV
in the folder NIR_Test_Logs_with_enclosure (next to this script).
Sensor LEDs are switched OFF so only the halogen lights the sample.
Install once:  pip install smbus2 --break-system-packages
"""

import csv
import os
import re
import struct
import time
from datetime import datetime

from smbus2 import SMBus

# ---------------- settings ----------------
I2C_BUS = 1
SENSOR_ADDR = 0x49
MUX_ADDR = 0x70
SENSOR_CHANNELS = [0, 1]   # mux channels your 2 sensors are on (change if different)

COUNTDOWN_S = 5
LOG_DURATION_S = 10
GAIN = 3                   # 0=1x, 1=3.7x, 2=16x, 3=64x (lower it if values saturate)
INT_TIME = 50              # integration time = INT_TIME x 2.8 ms

LOG_FOLDER = "NIR_Test_Logs_with_enclosure"
BANDS = ["R_610", "S_680", "T_730", "U_760", "V_810", "W_860"]
CAL_REGS = [0x14, 0x18, 0x1C, 0x20, 0x24, 0x28]

STATUS_REG, WRITE_REG, READ_REG = 0x00, 0x01, 0x02
TX_VALID, RX_VALID = 0x02, 0x01

bus = SMBus(I2C_BUS)


def select(ch):
    bus.write_byte(MUX_ADDR, 1 << ch)


def _wait(mask, want_set, timeout=1.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        status = bus.read_byte_data(SENSOR_ADDR, STATUS_REG)
        if bool(status & mask) == want_set:
            return
        time.sleep(0.001)
    raise TimeoutError("AS726x I2C timeout")


def read_virtual(reg):
    _wait(TX_VALID, False)
    bus.write_byte_data(SENSOR_ADDR, WRITE_REG, reg)
    _wait(RX_VALID, True)
    return bus.read_byte_data(SENSOR_ADDR, READ_REG)


def write_virtual(reg, value):
    _wait(TX_VALID, False)
    bus.write_byte_data(SENSOR_ADDR, WRITE_REG, reg | 0x80)
    _wait(TX_VALID, False)
    bus.write_byte_data(SENSOR_ADDR, WRITE_REG, value)


def read_float(reg):
    raw = bytes(read_virtual(reg + i) for i in range(4))
    return struct.unpack(">f", raw)[0]


def init_sensor(ch):
    select(ch)
    hw = read_virtual(0x00)
    print(f"Channel {ch}: hardware version 0x{hw:02X} (0x3F = AS7263)")
    write_virtual(0x04, 0x80)          # soft reset
    time.sleep(1.0)
    write_virtual(0x07, 0x00)          # LEDs OFF
    write_virtual(0x05, INT_TIME)
    write_virtual(0x04, (GAIN << 4) | (0b10 << 2))   # continuous, all channels
    time.sleep(0.3)


def read_sensor(ch):
    select(ch)
    t0 = time.time()
    while not (read_virtual(0x04) & 0x02):
        if time.time() - t0 > 2.0:
            raise TimeoutError(f"Sensor on channel {ch} not ready")
        time.sleep(0.01)
    vals = [read_float(r) for r in CAL_REGS]
    write_virtual(0x04, read_virtual(0x04) & ~0x02)  # clear DATA_RDY
    return vals


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text.strip())[:40] or "test"


def main():
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), LOG_FOLDER)
    os.makedirs(folder, exist_ok=True)

    for ch in SENSOR_CHANNELS:
        init_sensor(ch)

    note = input("Test note (e.g. eg1_PVC1_halogen): ").strip()
    for s in range(COUNTDOWN_S, 0, -1):
        print(f"Starting in {s}...")
        time.sleep(1)

    header = ["timestamp", "elapsed_s", "note"]
    for i, _ in enumerate(SENSOR_CHANNELS, start=1):
        header += [f"NIR{i}_{b}" for b in BANDS]

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, f"{stamp}_{safe_name(note)}.csv")

    rows = []
    t_start = time.time()
    while time.time() - t_start < LOG_DURATION_S:
        row_vals = []
        for ch in SENSOR_CHANNELS:
            row_vals += [round(v, 3) for v in read_sensor(ch)]
        t = time.time() - t_start
        rows.append([datetime.now().isoformat(timespec="milliseconds"), round(t, 3), note] + row_vals)
        print(f"{t:5.1f}s  " + "  ".join(f"{v:9.1f}" for v in row_vals))

    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

    print(f"\nSaved {len(rows)} samples to {path}")


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            bus.write_byte(MUX_ADDR, 0x00)   # all mux channels off
        except Exception:
            pass
        bus.close()
