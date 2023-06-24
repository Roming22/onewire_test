"""
Minimum amount of code required to start flashing the controller and extension board.
"""
import board as pin
import neopixel
import random
import storage

from time import sleep


class Board:
    def __init__(self):
        self.data = None
        self.pixels = None


def make_board():
    board = Board()
    board.pixels = neopixel.NeoPixel(pin.D0, 4)
    board.data = pin.D1
    return board


def get_color_func():
    drive_name = storage.getmount("/").label
    if drive_name.endswith("R"):

        def func():
            return (0, random.randint(0, 255), 0)

    else:

        def func():
            return (random.randint(0, 255), 0, 0)

    return func


def main() -> None:
    board = make_board()

    get_color = get_color_func()

    while True:
        board.pixels.fill(get_color())
        sleep(0.5)


if __name__ == "__main__":
    main()
