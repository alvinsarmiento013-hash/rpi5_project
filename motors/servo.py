#!/usr/bin/env python3
# MG996R Servo Motor Test - 3 Servos
# GPIO 18, 23, 24

import warnings
warnings.filterwarnings("ignore")
import RPi.GPIO as GPIO
import time

# Configuration
SERVO_PINS = [18, 23, 24]
FREQUENCY = 50

MIN_DUTY = 2.5
MID_DUTY = 7.5
MAX_DUTY = 12.5

def angle_to_duty(angle):
    return MIN_DUTY + (angle / 180.0) * (MAX_DUTY - MIN_DUTY)

def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    pwm_list = []
    for pin in SERVO_PINS:
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, FREQUENCY)
        pwm.start(MID_DUTY)
        pwm_list.append(pwm)
    return pwm_list

def move_all(pwm_list, angle):
    for pwm in pwm_list:
        pwm.ChangeDutyCycle(angle_to_duty(angle))

def test_servos(pwm_list):
    print("Testing 3 x MG996R Servos on GPIO 18, 23, 24")
    time.sleep(1)

    print("Moving all to 0 degrees...")
    move_all(pwm_list, 0)
    time.sleep(1)

    print("Moving all to 90 degrees...")
    move_all(pwm_list, 90)
    time.sleep(1)

    print("Moving all to 180 degrees...")
    move_all(pwm_list, 180)
    time.sleep(1)

    print("Sweeping all 0 to 180...")
    for angle in range(0, 181, 5):
        move_all(pwm_list, angle)
        print(f"  Angle: {angle}")
        time.sleep(0.05)

    print("Sweeping all 180 to 0...")
    for angle in range(180, -1, -5):
        move_all(pwm_list, angle)
        print(f"  Angle: {angle}")
        time.sleep(0.05)

    print("Returning all to center...")
    move_all(pwm_list, 90)
    time.sleep(1)
    print("Test complete!")

def cleanup(pwm_list):
    for pwm in pwm_list:
        pwm.ChangeDutyCycle(0)
        pwm.stop()
    GPIO.cleanup()

if __name__ == "__main__":
    pwm_list = setup()
    try:
        test_servos(pwm_list)
    except KeyboardInterrupt:
        print("\nStopped by user!")
    finally:
        cleanup(pwm_list)
        print("GPIO cleaned up!")