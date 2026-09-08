"""
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
