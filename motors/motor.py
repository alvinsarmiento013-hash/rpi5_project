#!/usr/bin/env python3
"""
motor_test.py - HW-039 (BTS7960) motor test, Raspberry Pi 5
Wiring: RPWM -> GPIO18, R_EN -> GPIO23, L_EN -> tied to R_EN (or 3.3V),
        LPWM -> GND, VCC -> Pi 5V, GND -> Pi GND (common with 12V supply).
Install once:  sudo apt install python3-gpiozero python3-lgpio -y
"""

import time
from gpiozero import PWMOutputDevice, DigitalOutputDevice

RPWM_PIN = 18
R_EN_PIN = 23
PWM_FREQ = 1000        # Hz
RUN_SPEED = 0.5        # 0.0-1.0 (start low, e.g. 0.3)
RUN_SECONDS = 5
RAMP_SECONDS = 2

rpwm = PWMOutputDevice(RPWM_PIN, frequency=PWM_FREQ, initial_value=0)
r_en = DigitalOutputDevice(R_EN_PIN, initial_value=False)


def ramp(start, end, seconds, steps=40):
    for i in range(steps + 1):
        rpwm.value = start + (end - start) * i / steps
        time.sleep(seconds / steps)


try:
    input("Check wiring and the 12V supply. Press Enter to start (Ctrl+C to stop)...")
    r_en.on()                       # enable the driver
    print(f"Ramping up to {RUN_SPEED:.0%}...")
    ramp(0, RUN_SPEED, RAMP_SECONDS)
    print(f"Running for {RUN_SECONDS} s...")
    time.sleep(RUN_SECONDS)
    print("Ramping down...")
    ramp(RUN_SPEED, 0, RAMP_SECONDS)
    print("Done.")
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    rpwm.value = 0
    r_en.off()
    rpwm.close()
    r_en.close()
