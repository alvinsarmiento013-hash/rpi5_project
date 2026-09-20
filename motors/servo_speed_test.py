"""
Swing arm simulation: 4 servos rest at 180, swing to 90 at adjustable speed, return to 180 and hold.
Triggered together by a single button press.
"""

import time
from gpiozero import AngularServo, Button
from gpiozero.pins.lgpio import LGPIOFactory

# ---- CONFIG ----
SERVO_PINS = [18, 13, 12, 19]
BUTTON_PIN = 15
REST_ANGLE = 180
SWING_ANGLE = 90
HOLD_AT_SWING = 1.5
REST_SETTLE = 1.0

SPEED = 100          # 1-100. 100 = fastest (direct jump), lower = slower stepped movement
STEP_SIZE = 2         # degrees per step when speed < 100 (smaller = smoother but more steps)

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

button = Button(BUTTON_PIN, pin_factory=factory)

def move_all(target_angle, speed=SPEED):
    """Move all servos to target_angle. speed=100 jumps directly (max mechanical speed).
    Lower speed steps through intermediate angles with a delay, simulating slower motion."""
    if speed >= 100:
        for s in servos:
            s.angle = target_angle
        return

    # delay per step scales inversely with speed: lower speed = longer delay
    # at speed=1, delay is largest; at speed=99, delay is tiny (near-instant)
    delay_per_step = (100 - speed) / 100 * 0.05   # tune 0.05 to taste

    # step each servo from its current angle toward target
    current_angles = [s.angle if s.angle is not None else REST_ANGLE for s in servos]
    steps_needed = max(
        abs(target_angle - cur) for cur in current_angles
    ) / STEP_SIZE
    steps_needed = max(1, int(steps_needed))

    for step in range(1, steps_needed + 1):
        for i, s in enumerate(servos):
            start = current_angles[i]
            new_angle = start + (target_angle - start) * (step / steps_needed)
            s.angle = new_angle
        time.sleep(delay_per_step)

def swing_cycle():
    move_all(SWING_ANGLE, SPEED)
    time.sleep(HOLD_AT_SWING)
    move_all(REST_ANGLE, SPEED)
    time.sleep(REST_SETTLE)

def main():
    print(f"Resting all servos at {REST_ANGLE} degrees. Speed set to {SPEED}%. Waiting for button presses...")
    move_all(REST_ANGLE, speed=100)   # snap to rest instantly on startup
    time.sleep(1)

    while True:
        button.wait_for_press()
        print(f"Button pressed — swinging all servos at speed {SPEED}%.")
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
