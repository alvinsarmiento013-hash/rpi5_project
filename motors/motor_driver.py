"""
DC Motor test via BTS7960 (HW-039) motor driver — single direction only,
using only R_EN and RPWM (LPWM/L_EN left unused).

Wiring:
  Driver R_EN  -> Pi GPIO23 (enable pin, on/off)
  Driver RPWM  -> Pi GPIO18 (PWM speed control)
  Driver LPWM, L_EN -> leave unconnected (not used for single-direction test)
  Driver VCC   -> Pi 3.3V or 5V (logic supply — check your board's spec)
  Driver GND   -> common ground with Pi
  Driver B+/B- -> your 12V motor power supply
  Driver M+/M- -> motor terminals
"""

import time
from gpiozero import DigitalOutputDevice, PWMOutputDevice
from gpiozero.pins.lgpio import LGPIOFactory

R_EN_PIN = 23
RPWM_PIN = 18

factory = LGPIOFactory()

r_en = DigitalOutputDevice(R_EN_PIN, pin_factory=factory)
rpwm = PWMOutputDevice(RPWM_PIN, frequency=1000, pin_factory=factory)


def run_motor(speed, duration):
    """speed: 0.0 (off) to 1.0 (full speed)"""
    r_en.on()
    rpwm.value = speed
    time.sleep(duration)
    rpwm.value = 0
    r_en.off()


def main():
    print("Testing motor via R_EN + RPWM only (single direction).")
    try:
        print("Running at 50% speed for 3 seconds...")
        run_motor(0.5, 3)
        time.sleep(1)

        print("Running at 100% speed for 3 seconds...")
        run_motor(1.0, 3)

        print("Done.")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        rpwm.value = 0
        r_en.off()


if __name__ == "__main__":
    main()
