"""
Minimum amount of code required to start flashing the controller and extension board.
"""
import adafruit_logging as logging
import board
import digitalio
import gc
import neopixel
import random
import storage
import supervisor

from microcontroller import delay_us
from time import sleep


logger = logging.Logger("logger")
logger.setLevel(logging.INFO)

"""
Controller: board connected to USB to the computer.
Extension:  board receiving power from the Controller. Not connected to the computer.
"""


frequency = 12000


class Board:
    def __init__(self):
        """Setup the board

        Set time between blinks.
        Open communication channel.
        Set LEDs colors. The controller blinks red/green depending if it is on the
        left or right side.
        """
        # The sleep is needed to wait for the board to finish initializing
        sleep(1)
        self.is_extension = not supervisor.runtime.usb_connected
        self.sleep = 0.3

        # Open the communication channel
        self.channel = BitBangProtocol(board.D1, frequency)

        # Set LEDs color
        self.pixels = neopixel.NeoPixel(board.D0, 4)
        if storage.getmount("/").label.endswith("L"):
            self.color = (255, 0, 0)
        else:
            self.color = (0, 255, 0)
        self.pixels.fill((15, 15, 15))

        logger.info("Board OK")

    def blink(self, follow_extension: bool):
        """Test half-duplex communication

        A board blinks for a random number of time, then pass the value to the other
        board. The other board then performs then blinks the same number of time.

        The follower blinks blue.

        This demonstrate synchronization and passing data between the boards.
        """
        is_follower = self.is_extension != follow_extension
        if is_follower:
            self.color = (0, 0, 255)

        msg_length = 3
        if is_follower:
            count = 0
        else:
            count = random.randint(1, 2**msg_length - 1)
        logger.info(
            "Follower: %s (%s , %s)", is_follower, self.is_extension, follow_extension
        )

        count = 0
        while True:
            logger.info("Waiting for go...")
            if is_follower:
                self.pixels.fill((15, 0, 15))
                count = self.channel.receive(msg_length)
                self.pixels.fill((0, 0, 0))
            else:
                if count:
                    self.pixels.fill((15, 15, 15))
                    self.channel.receive()
                count = random.randint(1, 2**msg_length - 1)
                self.pixels.fill((0, 0, 0))

            logger.info("Blink")
            sleep(self.sleep*3)
            for _ in range(count):
                self.pixels.fill(self.color)
                sleep(self.sleep)
                self.pixels.fill((0, 0, 0))
                sleep(self.sleep)

            logger.info("Send go")
            if is_follower:
                self.channel.send()
            else:
                self.channel.send(count, msg_length)


# Bit-banging communication class
class BitBangProtocol:
    """Protocol to connect 2 devices through a single wire.

    The connection is half-duplex. The receiving device is expected to already
    be listening when another device is sending a message.

    A frame is divided in 3 equal ticks.
    By default the bus is HIGH.
    On the first tick the bus is set to LOW. This is interreted by the receiver
    as the signal that a new frame is starting.
    On the second tick the bus is set to the value of the bit that is transmitted
    (LOW for 0, HIGH for 1).
    On the third tick the bus is reset to HIGH.

       _     _      _   ___
    0:  |___|    1:  |_|
        1 2 3        1 2 3

    The first and last tick allow the receiver to stay synchronized with the sender.

    Each message contains a start and end frame.
    """

    def __init__(self, pin, frequency: int):
        self.gpio = digitalio.DigitalInOut(pin)
        self.gpio.switch_to_output()
        self.gpio.value = True
        self.tick = 10**6 // (frequency * 3)

    def _handshake_send(self):
        pass

    def _handshake_receive(self):
        pass

    def send(self, value=0, length=0):
        """Send data

        Can be called with no parameters as a way to synchronize the boards."""
        bits = [(value >> i) & 1 for i in range(length)]
        logger.info("Sending %s as %s...", value, bits)

        self._handshake_send()

        # Add start/end frames
        bits.insert(0, False)
        bits.append(True)

        # Send frames
        for bit in bits:
            # Tick 1
            self.gpio.value = False
            delay_us(self.tick)
            # Tick 2-3
            self.gpio.value = bit
            delay_us(self.tick*2)
            # Tick 4
            self.gpio.value = True
            delay_us(self.tick)
        logger.info("Data sent")

    def receive(self, length: int = 0) -> int:
        """Receive data

        Can be called with no parameters as a way to synchronize the boards."""
        logger.info("Receiving %s bits", length)
        self.gpio.switch_to_input(digitalio.Pull.UP)
        bits = 0 << (length + 1)

        self._handshake_receive()

        # Receive frames
        tick = int(self.tick * 1.5)
        for index in range(length + 2):
            # Receive frame
            while self.gpio.value != False:
                pass
            delay_us(tick)
            bits |= self.gpio.value << index
            while self.gpio.value != True:
                pass

        self.gpio.switch_to_output(True, digitalio.DriveMode.OPEN_DRAIN)

        # Return value
        if length == 0:
            bits = 0
        else:
            bits &= ~(1 << index)
            bits >>= 1
        logger.info("Received: %s", bits)
        return bits


def main() -> None:
    board = Board()
    board.blink(follow_extension=False)


if __name__ == "__main__":
    main()
