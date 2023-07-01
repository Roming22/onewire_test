"""
Minimum amount of code required to start flashing the controller and extension board.
"""
import adafruit_logging as logging
import board
import digitalio
import neopixel
import random
import storage
import supervisor

from time import sleep


logger = logging.Logger("logger")
logger.setLevel(logging.INFO)

"""
Controller: board connected to USB to the computer.
Extension:  board receiving power from the Controller. Not connected to the computer.
"""


frequency = 5000


class Board:
    def __init__(self):
        """Setup the board

        Set time between blinks.
        Open communication channel.
        Set LEDs colors. The controller blinks red/green depending if it is on the
        left or right side. The extension blinks blue.
        """
        # The sleep is needed to wait for the board to finish initializing
        sleep(0.4)
        self.is_extension = not supervisor.runtime.usb_connected
        self.sleep = 0.1

        # Open the communication channel
        self.channel = BitBangProtocol(board.D1, frequency)

        # Set LEDs color
        self.pixels = neopixel.NeoPixel(board.D0, 4)
        if self.is_extension:
            self.color = (0, 0, 255)
        elif storage.getmount("/").label.endswith("L"):
            self.color = (255, 0, 0)
        else:
            self.color = (0, 255, 0)

        logger.info("Board OK")

    def blink(self, follow_extension: bool):
        """Test half-duplex communication

        A board blinks for a random amount of time, then pass the signal to the other
        board. The other board then performs the same action.

        This demonstrate synchronization between the boards.
        """
        wait = self.is_extension != follow_extension
        self.pixels.fill((15, 0, 15))

        if wait:
            sleep(2)

        while True:
            logger.info("Waiting for go...")
            self.channel.receive(wait)

            logger.info("Blink")
            self.pixels.fill(self.color)
            sleep(self.sleep * random.randint(1, 10))
            self.pixels.fill((0, 0, 0))

            logger.info("Send go")
            wait = True
            self.channel.send()


# Bit-banging communication class
class BitBangProtocol:
    def __init__(self, pin, frequency: int):
        self.gpio = digitalio.DigitalInOut(pin)
        self.delay = 1 / frequency

    def send(self):
        self.gpio.switch_to_output()
        for bit in [False, True]:
            self.gpio.value = bit
            sleep(self.delay)

    def receive(self, wait):
        while wait:
            wait = self.gpio.value
            sleep(self.delay)


def main() -> None:
    board = Board()
    board.blink(follow_extension=True)


if __name__ == "__main__":
    main()
