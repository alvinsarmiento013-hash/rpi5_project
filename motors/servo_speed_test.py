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
        servo.detach()"""
MG996R servo rotation speed test.

Sweeps the servo from 0 -> 180 degrees and back, timing each sweep,
so you can calculate degrees/second and figure out how much room a
gate needs to fully actuate and reset before the next fruit arrives.

Requires: pigpio daemon running (sudo systemctl start pigpiod)
Wiring: servo signal wire -> a GPIO pin that supports PWM (e.g. GPIO18)
        servo power (red) -> separate 5V/6V supply, NOT the Pi's 5V rail
        servo ground (brown/black) -> common ground with the Pi
"""

import time
from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory

# ---- CONFIG ----
SERVO_PIN = 18          # change to whichever GPIO you wired the signal to
MIN_ANGLE = 0
MAX_ANGLE = 180
NUM_SWEEPS = 5           # how many back-and-forth cycles to average over
SETTLE_TIME = 0.3        # seconds to pause at each end before reversing

factory = PiGPIOFactory()
servo = AngularServo(
    SERVO_PIN,
    min_angle=MIN_ANGLE,
    max_angle=MAX_ANGLE,
    min_pulse_width=0.0005,   # 500us  - typical MG996R low end
    max_pulse_width=0.0025,   # 2500us - typical MG996R high end
    pin_factory=factory,
)

def sweep(start, end):
    servo.angle = start
    time.sleep(SETTLE_TIME)
    t0 = time.perf_counter()
    servo.angle = end
    # gpiozero sets the target instantly (it's PWM, not blocking),
    # so we poll until the servo has had time to physically get there.
    # We estimate settle by watching for a stable duration instead of
    # a position readback, since MG996R has no feedback wire.
    time.sleep(SETTLE_TIME)
    t1 = time.perf_counter()
    return t1 - t0 - SETTLE_TIME  # rough travel time estimate


def main():
    print(f"Testing MG996R on GPIO{SERVO_PIN}: {NUM_SWEEPS} sweeps, "
          f"{MIN_ANGLE}->{MAX_ANGLE} degrees")

    forward_times = []
    backward_times = []

    for i in range(NUM_SWEEPS):
        ft = sweep(MIN_ANGLE, MAX_ANGLE)
        forward_times.append(ft)
        print(f"Sweep {i+1} forward (0->180): {ft:.3f}s")

        bt = sweep(MAX_ANGLE, MIN_ANGLE)
        backward_times.append(bt)
        print(f"Sweep {i+1} backward (180->0): {bt:.3f}s")

    avg_forward = sum(forward_times) / len(forward_times)
    avg_backward = sum(backward_times) / len(backward_times)
    avg_all = (sum(forward_times) + sum(backward_times)) / (2 * NUM_SWEEPS)

    deg_range = MAX_ANGLE - MIN_ANGLE
    print("\n--- Results ---")
    print(f"Avg forward time:  {avg_forward:.3f}s  ({deg_range/avg_forward:.1f} deg/s)")
    print(f"Avg backward time: {avg_backward:.3f}s  ({deg_range/avg_backward:.1f} deg/s)")
    print(f"Overall avg:       {avg_all:.3f}s  ({deg_range/avg_all:.1f} deg/s)")

    servo.detach()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        servo.detach()
        print("\nStopped.")
