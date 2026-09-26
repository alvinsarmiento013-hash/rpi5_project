"""
HX711 + Load Cell — Live Terminal Test (no file output)

Prints raw readings continuously to the terminal so you can watch values
change in real time as you press/release the load cell. Press Ctrl+C to stop.

Wiring:
  HX711 VCC -> Pi 5V (or 3.3V, check your specific HX711 board's rating)
  HX711 GND -> Pi GND
  HX711 DT  -> Pi GPIO5 (change DT_PIN below if wired elsewhere)
  HX711 SCK -> Pi GPIO6 (change SCK_PIN below if wired elsewhere)
  Load cell's 4 wires (red/black/white/green typically) -> HX711's
  E+/E-/A+/A- terminals per the load cell's own color-coding/datasheet

This talks to the HX711 directly over its native 2-wire protocol using
lgpio (same library already used for the servos), so no extra HX711
library is required.
"""

import lgpio
import time

DT_PIN = 5
SCK_PIN = 6

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, SCK_PIN)
lgpio.gpio_claim_input(h, DT_PIN)


def read_raw():
    # wait until the HX711 signals data is ready (DT goes low)
    while lgpio.gpio_read(h, DT_PIN) == 1:
        time.sleep(0.001)

    count = 0
    for _ in range(24):
        lgpio.gpio_write(h, SCK_PIN, 1)
        count = count << 1
        lgpio.gpio_write(h, SCK_PIN, 0)
        if lgpio.gpio_read(h, DT_PIN):
            count += 1

    # 25th pulse: sets gain=128, channel A for the NEXT reading
    lgpio.gpio_write(h, SCK_PIN, 1)
    lgpio.gpio_write(h, SCK_PIN, 0)

    # convert 24-bit two's complement to a signed integer
    if count & 0x800000:
        count -= 0x1000000

    return count


def main():
    print("Reading load cell — live values below. Press Ctrl+C to stop.\n")
    try:
        while True:
            val = read_raw()
            print(f"Raw: {val}")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        lgpio.gpiochip_close(h)


if __name__ == "__main__":
    main()
