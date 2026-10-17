
"""
LIFELANE - Smart Traffic Light System for Emergency Vehicles

Reference implementation for a Raspberry Pi 4 prototype.

Assumptions:
- MFRC522-compatible SPI RFID reader
- Two traffic signal units, each with red, yellow and green LEDs
- One active-high buzzer driver input

This code is a starter example, not tested against the supplied circuit.
Verify all GPIO assignments and hardware connections before use.
"""

import time
import signal
import sys

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522


# BCM GPIO numbering
TRAFFIC_1 = {"red": 17, "yellow": 27, "green": 22}
TRAFFIC_2 = {"red": 23, "yellow": 24, "green": 25}
BUZZER = 18

# Replace these example IDs with your own RFID tag IDs.
# Map each authorized tag to the lane it should prioritize.
AUTHORIZED_TAGS = {
    123456789: 1,
    987654321: 2,
}

NORMAL_GREEN_SECONDS = 5
YELLOW_SECONDS = 2
BUZZER_SECONDS = 1


def set_light(signal_unit, color):
    """Turn off a signal unit's LEDs, then enable the selected color."""
    for pin in signal_unit.values():
        GPIO.output(pin, GPIO.LOW)

    if color is not None:
        GPIO.output(signal_unit[color], GPIO.HIGH)


def set_both_red():
    """Stop both prototype traffic directions."""
    set_light(TRAFFIC_1, "red")
    set_light(TRAFFIC_2, "red")


def normal_sequence():
    """Demonstration sequence for two conflicting directions."""
    set_light(TRAFFIC_1, "green")
    set_light(TRAFFIC_2, "red")
    time.sleep(NORMAL_GREEN_SECONDS)

    set_light(TRAFFIC_1, "yellow")
    time.sleep(YELLOW_SECONDS)

    set_both_red()
    time.sleep(1)

    set_light(TRAFFIC_2, "green")
    set_light(TRAFFIC_1, "red")
    time.sleep(NORMAL_GREEN_SECONDS)

    set_light(TRAFFIC_2, "yellow")
    time.sleep(YELLOW_SECONDS)

    set_both_red()
    time.sleep(1)


def emergency_sequence(lane):
    """
    Demonstrate priority for one lane.

    Both directions are set red before the priority lane turns green.
    This is simplified bench-test logic and is not a certified
    traffic signal safety controller.
    """
    print(f"Authorized emergency tag: prioritizing lane {lane}")

    set_both_red()
    time.sleep(2)

    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(BUZZER_SECONDS)
    GPIO.output(BUZZER, GPIO.LOW)

    if lane == 1:
        set_light(TRAFFIC_1, "green")
        set_light(TRAFFIC_2, "red")
    else:
        set_light(TRAFFIC_2, "green")
        set_light(TRAFFIC_1, "red")

    # Demonstration priority interval
    time.sleep(5)

    # Return to a safe stopped state before normal operation resumes.
    set_both_red()
    time.sleep(2)


def cleanup(signum=None, frame=None):
    """Turn off outputs and release GPIO resources."""
    print("\nStopping LIFELANE prototype...")

    try:
        GPIO.output(BUZZER, GPIO.LOW)
        set_both_red()

        # Turn off all LEDs during shutdown.
        for signal_unit in (TRAFFIC_1, TRAFFIC_2):
            for pin in signal_unit.values():
                GPIO.output(pin, GPIO.LOW)
    except Exception:
        pass
    finally:
        GPIO.cleanup()
        sys.exit(0)


def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    for signal_unit in (TRAFFIC_1, TRAFFIC_2):
        for pin in signal_unit.values():
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

    GPIO.setup(BUZZER, GPIO.OUT, initial=GPIO.LOW)

    # Start in an all-red state.
    set_both_red()

    reader = SimpleMFRC522()

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("LIFELANE started. Present an RFID tag to the reader.")

    try:
        while True:
            tag_id = reader.read_id_no_block()

            if tag_id is not None:
                lane = AUTHORIZED_TAGS.get(int(tag_id))

                if lane in (1, 2):
                    emergency_sequence(lane)
                else:
                    print("Unknown or unauthorized RFID tag.")

                # Simple debounce to avoid repeated reads.
                time.sleep(1)
            else:
                normal_sequence()

    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
