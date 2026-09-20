"""
Swing arm simulation: servo rests at 180, swings fast to 90, returns to 180 and holds.
Triggered by a button press instead of running automatically.

Wiring:
  Servo signal -> GPIO18 (PWM)
  Servo power (red) -> separate 5V/6V supply, NOT the Pi's 5V rail
  Servo ground -> common ground with the Pi

  Button leg 1 -> GPIO15 (BCM)
  Button leg 2 -> any GND pin on the Pi
  (uses internal pull-up: pin reads HIGH normally, LOW when pressed)
"""

import time
from gpiozero import AngularServo, Button
from gpiozero.pins.lgpio import LGPIOFactory

# ---- CONFIG ----
SERVO_PIN = 18
BUTTON_PIN = 15
REST_ANGLE = 180
SWING_ANGLE = 90
HOLD_AT_SWING = 0.2      # seconds to pause at 90 before returning
REST_SETTLE = 0.5        # seconds to settle at rest before accepting next press

factory = LGPIOFactory()

servo = AngularServo(
    SERVO_PIN,
    min_angle=0,
    max_angle=180,
    min_pulse_width=0.0005,
    max_pulse_width=0.0025,
    pin_factory=factory,
)

button = Button(BUTTON_PIN, pin_factory=factory)  # pull_up=True by default

def swing_cycle():
    servo.angle = SWING_ANGLE          # fast move to 90
    time.sleep(HOLD_AT_SWING)          # brief pause at 90
    servo.angle = REST_ANGLE           # return to 180
    time.sleep(REST_SETTLE)            # settle time at rest before accepting next press

def main():
    print(f"Resting at {REST_ANGLE} degrees. Waiting for button presses...")
    servo.angle = REST_ANGLE
    time.sleep(1)

    while True:
        button.wait_for_press()
        print("Button pressed — swinging.")
        swing_cycle()
        print(f"Back at rest ({REST_ANGLE}). Waiting for next press...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        servo.detach()
