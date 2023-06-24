"""
Minimum amount of code required to start flashing the controller and extension board.
"""
import board as pin
import neopixel
import random
import storage
import supervisor

from time import sleep


class Board:
    def __init__(self):
        self.data = None
        self.pixels = None
        self.sleep = 5


def make_board():
    board = Board()
    board.pixels = neopixel.NeoPixel(pin.D0, 4)
    board.data = pin.D1
    if supervisor.runtime.usb_connected:
        board.sleep = 0.5
    else:
        board.sleep = 2
    return board


def get_color_func():
    drive_name = storage.getmount("/").label
    if drive_name.endswith("R"):

        def func():
            return (0, 32 * random.randint(1, 8) - 1, 0)

    else:

        def func():
            return (32 * random.randint(1, 8) - 1, 0, 0)

    return func


def main() -> None:
    board = make_board()

    get_color = get_color_func()

    while True:
        board.pixels.fill(get_color())
        sleep(board.sleep)


if __name__ == "__main__":
    main()
