import random
from array import array
from time import sleep

import adafruit_logging as logging
import board
import neopixel
import pulseio
import storage
import supervisor

logger = logging.Logger("logger")
logger.setLevel(logging.INFO)

"""
Controller: board connected to USB to the computer.
Extension:  board receiving power from the Controller. Not connected to the computer.
"""


class Board:
    def __init__(self):
        """Setup the board
        Set LEDs colors.
        """
        # The sleep is needed to wait for the board to finish initializing
        sleep(1)
        self.is_extension = not supervisor.runtime.usb_connected
        self.is_extension = storage.getmount("/").label.endswith("R")

        # Set LEDs color
        self.pixels = neopixel.NeoPixel(board.D0, 4)
        if storage.getmount("/").label.endswith("L"):
            self.color = (255, 0, 0)
        else:
            self.color = (0, 255, 0)
        self.pixels.fill((15, 15, 15))

        logger.info("Board OK")

    def run(self):
        if self.is_extension:
            logger.info("Sending data")
            with pulseio.PulseOut(board.D1) as pulse:
                pulses_list = [
                    array("H", [11111, 22222, 11111, 22222, 11111]),
                    array("H", [1111, 2222, 1111, 2222, 1111]),
                    array("H", [111, 222, 111, 222, 111]),
                ]
                while True:
                    for pulses in pulses_list:
                        pulse.send(pulses)
                        sleep(3)
                    sleep(2)
        else:
            logger.info("Receiving data")
            with pulseio.PulseIn(board.D1, 2**10) as pulses:
                while True:
                    if len(pulses) > 0:
                        logger.info("%s", [pulses[i] for i in range(len(pulses))])
                        pulses.clear()


def main() -> None:
    board = Board()
    board.run()


if __name__ == "__main__":
    main()
