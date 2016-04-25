#!/usr/bin/python3
"""Virtual 8x8 LED grid implemented in pygame.

LED Grid -         Copyright 2016 Zeth
8x8GridDraw -      Copyright 2015 Richard Hayler
Python Sense Hat - Copyright 2015 Raspberry Pi Foundation

The interface aims to be similar to the public interface of the
Raspberry Pi Sense HAT library, such that it is useful in mocking up
software for it and other such devices.

The implementation however is rather simpler.

Many thanks to Richard Hayler.
The LED class, graphics, etc are based on 8x8GridDraw
https://github.com/topshed/RPi_8x8GridDraw
http://richardhayler.blogspot.co.uk/2015/06/creating-images-for-astro-pi-hat.html

It should work anywhere pygame can run, if not then it is a bug,
please tell me.

So far I have tested it on:

* Debian Jessie AMD64 Python 3.5/2.7
* Raspbian Wheezy 3.2 on Raspberry Pi 2
* Raspbian Jessie 2.7/3.4 on Raspberry Pi 3
* Raspbian Stretch 2.7/3.4 on Raspberry Pi 3

This should work on all versions of Python 3 as well as your grandma's
Python 2.7. If not then it is a bug, please let me know.

"""

# Compatibility for old souls using Python 2 in their
# zeppelins and chariots etc
from __future__ import division

import os

# Optional image support
try:
    from PIL import Image  # pillow
except ImportError:
    Image = None

import pygame


class LEDGrid(object):
    """This class provides an on-screen representation of an 8x8 RGB LED
    grid, as found in the Raspberry Pi Sense HAT and other products
    such as the Unicorn HAT.

    By default, setting colour of an LED to 0,0,0 will turn it off.
    If instead you want it to show a solid black, set black_is_colour=True

    If an existing pygame screen object is not provided then a basic
    little fixed screen is created. Use title argument to set the window
    title.

    TODO: make the basic screen size flexible.
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 black_is_colour=False,
                 screen=None,
                 title=None):
        self._black_is_colour = black_is_colour
        self._title = title or "LED Grid"
        self._rotation = 0
        self._leds = []  # The LED matrix
        self._pixels = [OFF] * 64  # The list of pixels
        self._basic = False
        self._background = None
        self._screen = screen
        if not screen:
            self._setup_basic_screen()
        else:
            self._setup_leds()

    @property
    def rotation(self):
        """The current rotation of the grid."""
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        """Set the current rotation of the grid."""
        self.set_rotation(rotation, True)

    def set_rotation(self, rotation=0, redraw=True):
        """Sets the LED matrix rotation for viewing, adjust if the Pi is
        upside down or sideways. 0 is with the Pi HDMI port facing
        downwards
        """
        if rotation in (0, 90, 180, 270):
            self._rotation = rotation
            if redraw:
                self.set_pixels(self._pixels)
        else:
            raise ValueError('Rotation must be 0, 90, 180 or 270 degrees')

    def flip_h(self, redraw=True):
        """
        Flip LED matrix horizontal
        """

        pixel_list = self.get_pixels()
        flipped = []
        for i in range(8):
            offset = i * 8
            flipped.extend(reversed(pixel_list[offset:offset + 8]))
        if redraw:
            self.set_pixels(flipped)
        return flipped

    def flip_v(self, redraw=True):
        """
        Flip LED matrix vertical
        """

        pixel_list = self.get_pixels()
        flipped = []
        for i in reversed(range(8)):
            offset = i * 8
            flipped.extend(pixel_list[offset:offset + 8])
        if redraw:
            self.set_pixels(flipped)
        return flipped

    def set_pixels(self, pixel_list):
        """
        Accepts a list containing 64 smaller lists of [R,G,B] pixels and
        updates the LED matrix. R,G,B elements must intergers between 0
        and 255
        """

        if len(pixel_list) != 64:
            raise ValueError('Pixel lists must have 64 elements')

        for index, pix in enumerate(pixel_list):
            if len(pix) != 3:
                raise ValueError(
                    'Pixel at index %d is invalid. '
                    'Pixels must contain 3 elements: '
                    'Red, Green and Blue' % index)

            for element in pix:
                if element > 255 or element < 0:
                    raise ValueError(
                        'Pixel at index %d is invalid. '
                        'Pixel elements must be between 0 and 255' % index)

        self._pixels = pixel_list

        for index, pix in enumerate(pixel_list):
            rot_index = self._rotate(index)
            self._leds[rot_index].colour = pix

        if self._basic:
            self._draw_basic_screen()

    def _rotate(self, index):
        """Rotate the data to the right direction.  Even seemingly un-rotated
        0 rotation needs work because what the SenseHAT's
        micro-controller expects is not what we (and pygame) expect.
        """
        led = self._leds[index]
        if self.rotation == 0:
            return (led.pos[1] * 8) + led.pos[0]
        elif self.rotation == 90:
            return ((7 - led.pos[0]) * 8) + led.pos[1]
        elif self.rotation == 180:
            return ((7 - led.pos[1]) * 8 +
                    (7 - led.pos[0]))
        elif self.rotation == 270:
            return (led.pos[0] * 8) + (7 - led.pos[1])
        else:
            raise ValueError('Rotation must be 0, 90, 180 or 270 degrees')

    def get_pixels(self):
        """
        Returns a list containing 64 smaller lists of [R,G,B] pixels
        representing what is currently displayed on the LED matrix
        """
        return self._pixels

    def set_pixel(self, x_pos, y_pos, *args):
        """Updates the single [R,G,B] pixel specified by x_pos and y_pos on
        the LED matrix Top left = 0,0 Bottom right = 7,7

        e.g. ap.set_pixel(x_pos, y_pos, r, g, b)
        or
        pixel = (r, g, b)
        ap.set_pixel(x_pos, y_pos, pixel)

        """
        pixel_error = 'Pixel arguments must be given as (r, g, b) or r, g, b'

        if len(args) == 1:
            pixel = args[0]
            if len(pixel) != 3:
                raise ValueError(pixel_error)
        elif len(args) == 3:
            pixel = args
        else:
            raise ValueError(pixel_error)

        if x_pos > 7 or x_pos < 0:
            raise ValueError('X position must be between 0 and 7')

        if y_pos > 7 or y_pos < 0:
            raise ValueError('Y position must be between 0 and 7')

        for element in pixel:
            if element > 255 or element < 0:
                raise ValueError('Pixel elements must be between 0 and 255')

        index = y_pos * 8 + x_pos
        self._pixels[index] = pixel
        led = self._leds[self._rotate(index)]
        led.colour = pixel

        if self._basic:
            self._draw_basic_screen()

    def get_pixel(self, x_pos, y_pos):
        """Returns a list of [R,G,B] representing the pixel specified by
        x_pos and y_pos on the LED matrix. Top left = 0,0 Bottom right
        = 7,7
        """

        if x_pos > 7 or x_pos < 0:
            raise ValueError('X position must be between 0 and 7')

        if y_pos > 7 or y_pos < 0:
            raise ValueError('Y position must be between 0 and 7')

        return self._get_pixel(x_pos, y_pos)

    def load_image(self, file_path, redraw=True):
        """
        Accepts a path to an 8 x 8 image file and updates the LED matrix with
        the image
        """
        if not Image:
            raise ImportError(
                "Need PIL implementation (e.g. pillow module) to use images.")
        if not os.path.exists(file_path):
            raise IOError('%s not found' % file_path)

        img = Image.open(file_path).convert('RGB')
        # pylint: disable=bad-builtin
        pixel_list = list(map(list, img.getdata()))

        if redraw:
            self.set_pixels(pixel_list)

        return pixel_list

    def clear(self, *args):
        """
        Clears the LED matrix with a single colour, default is black / off

        e.g. ap.clear()
        or
        ap.clear(r, g, b)
        or
        colour = (r, g, b)
        ap.clear(colour)
        """

        black = (0, 0, 0)  # default

        if len(args) == 0:
            colour = black
        elif len(args) == 1:
            colour = args[0]
        elif len(args) == 3:
            colour = args
        else:
            raise ValueError(
                'Pixel arguments must be given as (r, g, b) or r, g, b')

        self.set_pixels([colour] * 64)

    def _setup_basic_screen(self):
        """A basic pygame screen on which to show the LED grid."""
        self._basic = True
        pygame.init()  # pylint: disable=no-member
        pygame.display.set_caption(self._title)
        self._screen = pygame.display.set_mode((375, 375), 0, 32)
        # pylint: disable=too-many-function-args
        background = pygame.Surface(self._screen.get_size())
        self._background = background.convert()
        # Lets make background circuit board green
        self._background.fill((0, 51, 25))
        self._setup_leds()
        self._draw_basic_screen()

    def _draw_basic_screen(self):
        """(re-)Draw the screen."""

        self._screen.blit(self._background, (0, 0))
        self._draw_leds()
        pygame.display.flip()

    def _setup_leds(self):
        """Make a blank matrix of LEDs."""
        for rank in range(0, 8):
            for row in range(0, 8):
                led = LED(radius=20,
                          pos=(rank, row),
                          black_is_colour=self._black_is_colour,
                          screen=self._screen)
                self._leds.append(led)

    def _draw_leds(self):
        """Draw the LEDS."""
        for led in self._leds:
            led.draw()

    def _get_led(self, x_pos, y_pos):
        """Get an LED from a particular coordinate."""
        return self._leds[y_pos * 8 + x_pos]

    def _get_pixel(self, x_pos, y_pos):
        """Get a Pixel from a particular coordinate."""
        return self._pixels[y_pos * 8 + x_pos]


class LED(object):
    """A single virtual LED, shown using Pygame.
    By Richard Hayler, see note in module docstring above.
    """
    # pylint: disable=too-many-arguments, too-many-instance-attributes
    def __init__(self,
                 pos=(0, 0),
                 radius=25,
                 lit=False,
                 margins=(10, 10),
                 black_is_colour=False,
                 screen=None):
        # Initializes the LED
        self.pos = pos
        self.lit = lit
        self.radius = radius
        self._black_is_colour = black_is_colour
        self.screen = screen or pygame.display.get_surface()
        self._colour = WHITE
        self.pos_x = int(self.pos[0] * (self.radius * 2 +
                                        5)) + (self.radius) + margins[0]
        self.pos_y = int(self.pos[1] * (self.radius *
                                        2 + 5)) + (self.radius) + margins[1]

    @property
    def colour(self):
        """The current colour the LED."""
        return self._colour

    @colour.setter
    def colour(self, colour):
        """Set the current colour of the LED."""
        self._colour = colour
        if colour == tuple(OFF) and not self._black_is_colour:
            self.lit = False
        else:
            self.lit = True

    def draw(self):
        """Draws the LED."""
        # Draws a circle
        if self.lit:  # has it been clicked?
            thickness = 0
            colour = self._colour
        else:
            colour = WHITE
            thickness = 1

        pygame.draw.circle(
            self.screen,
            colour,
            (self.pos_x, self.pos_y),
            self.radius, thickness)

        # Draws a square
        pygame.draw.rect(
            self.screen,
            colour,
            (self.pos_x - self.radius,
             self.pos_y - self.radius,
             (2 * self.radius),
             (2 * self.radius)),
            thickness)

    def clicked(self, colour):
        """What to do when clicked/activated."""
        self.colour = colour
        if self.lit:
            self.lit = False
        else:
            self.lit = True

# Some friendly colours

RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
PURPLE = (102, 0, 204)
PINK = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
BLACK = OFF = (0, 0, 0)


EXAMPLE = (BLUE, BLUE, BLUE, BLUE, RED, OFF, OFF, OFF,
           BLUE, OFF, RED, RED, RED, OFF, OFF, OFF,
           BLUE, OFF, BLUE, BLUE, RED, OFF, OFF, OFF,
           BLUE, OFF, BLUE, BLUE, OFF, OFF, OFF, OFF,
           BLUE, RED, BLUE, BLUE, RED, OFF, OFF, OFF,
           RED, RED, RED, RED, BLUE, OFF, OFF, OFF,
           RED, RED, BLUE, BLUE, BLUE, OFF, OFF, OFF,
           OFF, OFF, OFF, BLUE, OFF, OFF, OFF, OFF)


def main():
    """Simple example."""
    grid = LEDGrid()
    grid.set_pixels(EXAMPLE)
    input()

if __name__ == '__main__':
    main()
