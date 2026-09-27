"""
HX711 + Load Cell — Live Weight in KG (no file output)

Calibrates on startup (tare + one known weight), then shows live kg
readings continuously. Press Ctrl+C to stop.
"""

import lgpio
import time

DT_PIN = 5
SCK_PIN = 6

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, SCK_PIN)
lgpio.gpio_claim_input(h, DT_PIN)


def read_raw():
    while lgpio.gpio_read(h, DT_PIN) == 1:
        time.sleep(0.001)

    count = 0
    for _ in range(24):
        lgpio.gpio_write(h, SCK_PIN, 1)
        count = count << 1
        lgpio.gpio_write(h, SCK_PIN, 0)
        if lgpio.gpio_read(h, DT_PIN):
            count += 1

    # 25th pulse: gain=128, channel A for next reading
    lgpio.gpio_write(h, SCK_PIN, 1)
    lgpio.gpio_write(h, SCK_PIN, 0)

    if count & 0x800000:
        count -= 0x1000000

    return count


def average_reading(samples=15):
    vals = [read_raw() for _ in range(samples)]
    return sum(vals) / len(vals)


def calibrate():
    input("Remove all weight from the load cell, then press Enter...")
    offset = average_reading()
    print(f"Zero offset (tare): {offset:.0f}")

    known_weight = float(input("Enter the known weight you'll place on it, in kg: "))
    input("Place that weight on the load cell now, then press Enter...")
    raw_with_weight = average_reading()

    scale_factor = (raw_with_weight - offset) / known_weight
    print(f"Scale factor: {scale_factor:.2f} counts/kg\n")
    return offset, scale_factor


def main():
    offset, scale_factor = calibrate()
    print("Calibration done. Showing live weight — press Ctrl+C to stop.\n")
    try:
        while True:
            raw = read_raw()
            kg = (raw - offset) / scale_factor
            print(f"Weight: {kg:.3f} kg")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        lgpio.gpiochip_close(h)


if __name__ == "__main__":
    main()
