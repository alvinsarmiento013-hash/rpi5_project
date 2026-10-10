#!/usr/bin/env python3
"""
nir_bench_test.py  -  AS7263 NIR bench test (Raspberry Pi 5)

Flow: ask for a test note -> 5 s countdown -> log for 10 s -> save one CSV per run
in the folder NIR_Test_Logs_with_enclosure (created next to this script).

The sensor's own LED is switched OFF so the halogen is the only light source.
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
SENSOR_ADDR = 0x49        # AS726x fixed address
MUX_ADDR = 0x70           # PCA9548A address
MUX_CHANNEL = None        # None = sensor wired directly; 0-7 = PCA9548A channel

COUNTDOWN_S = 5
LOG_DURATION_S = 10
GAIN = 3                  # 0=1x, 1=3.7x, 2=16x, 3=64x  (lower it if values saturate under halogen)
INT_TIME = 50             # integration time = INT_TIME x 2.8 ms (50 = 140 ms)

LOG_FOLDER = "NIR_Test_Logs_with_enclosure"
CHANNELS = ["R_610", "S_680", "T_730", "U_760", "V_810", "W_860"]
CAL_REGS = [0x14, 0x18, 0x1C, 0x20, 0x24, 0x28]   # calibrated float registers

# ---------------- AS726x low level ----------------
STATUS_REG, WRITE_REG, READ_REG = 0x00, 0x01, 0x02
TX_VALID, RX_VALID = 0x02, 0x01

bus = SMBus(I2C_BUS)


def select_mux():
    if MUX_CHANNEL is not None:
        bus.write_byte(MUX_ADDR, 1 << MUX_CHANNEL)


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


def init_sensor():
    select_mux()
    hw = read_virtual(0x00)
    print(f"Hardware version register: 0x{hw:02X} (0x3F = AS7263)")
    write_virtual(0x04, 0x80)          # soft reset
    time.sleep(1.0)
    write_virtual(0x07, 0x00)          # LED_CONTROL = 0 -> bulb LED and indicator LED OFF
    write_virtual(0x05, INT_TIME)      # integration time
    # CONTROL_SETUP: gain bits 5:4, bank/mode bits 3:2 = 0b10 (continuous, all channels)
    write_virtual(0x04, (GAIN << 4) | (0b10 << 2))
    time.sleep(0.3)


def _wait_ready(timeout=2.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if read_virtual(0x04) & 0x02:
            return
        time.sleep(0.01)
    raise TimeoutError("Sensor data not ready")


def read_channels():
    select_mux()
    _wait_ready()
    values = [read_float(r) for r in CAL_REGS]
    write_virtual(0x04, read_virtual(0x04) & ~0x02)   # clear DATA_RDY
    return values


# ---------------- test run ----------------
def safe_name(text):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text.strip())[:40] or "test"


def main():
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), LOG_FOLDER)
    os.makedirs(folder, exist_ok=True)

    init_sensor()
    note = input("Test note (e.g. eg1_PVC1_halogen): ").strip()

    for s in range(COUNTDOWN_S, 0, -1):
        print(f"Starting in {s}...")
        time.sleep(1)

    print(f"Logging for {LOG_DURATION_S} s...")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, f"{stamp}_{safe_name(note)}.csv")

    rows = []
    t_start = time.time()
    while time.time() - t_start < LOG_DURATION_S:
        vals = read_channels()
        t = time.time() - t_start
        rows.append([datetime.now().isoformat(timespec="milliseconds"), round(t, 3), note]
                    + [round(v, 3) for v in vals])
        print(f"{t:5.1f}s  " + "  ".join(f"{n}={v:9.1f}" for n, v in zip(CHANNELS, vals)))

    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "elapsed_s", "note"] + CHANNELS)
        w.writerows(rows)

    print(f"\nSaved {len(rows)} samples to {path}")


if __name__ == "__main__":
    try:
        main()
    finally:
        bus.close()
