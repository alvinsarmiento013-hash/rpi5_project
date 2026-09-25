"""
AS7263 EFSB Bench Test Data Logger
Based on efsb_nir_bench_test_plan.md — Part D data collection procedure

Each run of this script:
1. Asks for a test note (e.g. "testing near the stem 1")
2. Counts down 5 seconds before starting
3. Logs all 6 AS7263 channels + timestamp + temperature for a fixed
   10 seconds, then stops automatically (no key press needed)
4. Saves to a NEW file every run (named from your note + a timestamp,
   so nothing ever gets overwritten)

Wiring: VIN -> Pi 3.3V, GND -> Pi GND, SDA -> GPIO2, SCL -> GPIO3

Note on channel names: this uses the adafruit_as726x library, which
names its 6 channel properties violet/blue/green/yellow/orange/red
regardless of chip. On your AS7263 (confirmed via HW version 0x3f),
those same 6 properties actually correspond to the NIR wavelengths:
  violet -> R (~610nm)   yellow -> U (~760nm)
  blue   -> S (~680nm)   orange -> V (~810nm)
  green  -> T (~730nm)   red    -> W (~860nm)
"""

import time
import csv
import os
import board
import busio
from adafruit_as726x import AS726x_I2C

OUTPUT_DIR = "nir_test_logs"
LOG_DURATION_SECONDS = 10


def get_test_note():
    note = input("Enter test note (e.g. 'testing near the stem 1'): ").strip()
    if not note:
        note = "unnamed_test"
    return note


def countdown(seconds=5):
    print("\nStarting in:")
    for i in range(seconds, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print(f"GO — logging now for {LOG_DURATION_SECONDS} seconds. Move the fruit past the sensor.\n")


def make_filename(note):
    safe_note = "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in note)
    safe_note = safe_note.strip().replace(" ", "_")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return f"{safe_note}_{timestamp}.csv"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Connecting to AS7263...")
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = AS726x_I2C(i2c)
    print("Sensor connected!\n")

    # Light source substitute per Part A: onboard LED, since no halogen yet
    sensor.driver_led = True
    sensor.conversion_mode = sensor.MODE_2  # continuous, all 6 channels

    note = get_test_note()
    filename = make_filename(note)
    filepath = os.path.join(OUTPUT_DIR, filename)

    countdown(5)

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([f"test note: {note}"])
        writer.writerow(["data of the nir:"])
        writer.writerow([
            "timestamp", "R_610nm", "S_680nm", "T_730nm",
            "U_760nm", "V_810nm", "W_860nm", "temp_C",
        ])

        start_time = time.time()
        try:
            while time.time() - start_time < LOG_DURATION_SECONDS:
                if sensor.data_ready:
                    row = [
                        round(time.time(), 3),
                        sensor.violet,
                        sensor.blue,
                        sensor.green,
                        sensor.yellow,
                        sensor.orange,
                        sensor.red,
                        sensor.temperature,
                    ]
                    writer.writerow(row)
                    f.flush()
                    print(
                        f"{row[0]:.2f}  R:{row[1]:.1f} S:{row[2]:.1f} "
                        f"T:{row[3]:.1f} U:{row[4]:.1f} V:{row[5]:.1f} "
                        f"W:{row[6]:.1f}  {row[7]}C"
                    )
                time.sleep(0.05)
        finally:
            sensor.driver_led = False

    print(f"\nDone — {LOG_DURATION_SECONDS}s of data saved to: {filepath}")


if __name__ == "__main__":
    main()
