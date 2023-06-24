"""
Minimum amount of code required to start flashing the controller and extension board.
"""
import board as pin
import neopixel
import random
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


def main() -> None:
    board = make_board()

    while True:
        board.pixels.fill(
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        )
        sleep(2)


if __name__ == "__main__":
    main()
