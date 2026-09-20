"""
Swing arm simulation: 4 servos rest at 180, swing fast to 90, return to 180 and hold.
Triggered together by a single button press.

Wiring:
  Servo 1 signal -> GPIO18 (PWM)
  Servo 2 signal -> GPIO13 (PWM)
  Servo 3 signal -> GPIO12 (PWM)
  Servo 4 signal -> GPIO19 (PWM)
  All servo power (red) -> separate 5V/6V supply, NOT the Pi's 5V rail
  All servo grounds -> common ground with the Pi

  Button leg 1 -> GPIO15 (BCM)
  Button leg 2 -> any GND pin on the Pi
  (uses internal pull-up: pin reads HIGH normally, LOW when pressed)
"""

import time
from gpiozero import AngularServo, Button
from gpiozero.pins.lgpio import LGPIOFactory

# ---- CONFIG ----
SERVO_PINS = [18, 13, 12, 19]   # change to whichever GPIOs you wired each servo to
BUTTON_PIN = 15
REST_ANGLE = 180
SWING_ANGLE = 90
HOLD_AT_SWING = 0.2      # seconds to pause at 90 before returning
REST_SETTLE = 0.5        # seconds to settle at rest before accepting next press

factory = LGPIOFactory()

servos = [
    AngularServo(
        pin,
        min_angle=0,
        max_angle=180,
        min_pulse_width=0.0005,
        max_pulse_width=0.0025,
        pin_factory=factory,
    )
    for pin in SERVO_PINS
]

button = Button(BUTTON_PIN, pin_factory=factory)  # pull_up=True by default

def set_all(angle):
    for s in servos:
        s.angle = angle

def swing_cycle():
    set_all(SWING_ANGLE)               # all servos move to 90 together
    time.sleep(HOLD_AT_SWING)          # brief pause at 90
    set_all(REST_ANGLE)                # all servos return to 180 together
    time.sleep(REST_SETTLE)            # settle time before accepting next press

def main():
    print(f"Resting all servos at {REST_ANGLE} degrees. Waiting for button presses...")
    set_all(REST_ANGLE)
    time.sleep(1)

    while True:
        button.wait_for_press()
        print("Button pressed — swinging all servos.")
        swing_cycle()
        print(f"Back at rest ({REST_ANGLE}). Waiting for next press...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        for s in servos:
            s.detach()
