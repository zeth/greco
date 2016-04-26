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
import time
import base64
import io

import pygame
# Optional image support
try:
    from PIL import Image  # pillow
except ImportError:
    Image = None


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
        self._text_dict = {}
        self._load_text_assets()

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

    def _get_char_pixels(self, s):
        """
        Internal. Safeguards the character indexed dictionary for the
        show_message function below
        """

        if len(s) == 1 and s in self._text_dict.keys():
            return list(self._text_dict[s])
        else:
            return list(self._text_dict['?'])

    def show_message(self,
                     text_string,
                     scroll_speed=.1,
                     text_colour=(255, 255, 255),
                     back_colour=(0, 0, 0)):
        """
        Scrolls a string of text across the LED matrix using the specified
        speed and colours
        """

        # We must rotate the pixel map left through 90 degrees when drawing
        # text, see _load_text_assets
        previous_rotation = self._rotation
        self._rotation -= 90
        if self._rotation < 0:
            self._rotation = 270
        dummy_colour = [None, None, None]
        string_padding = [dummy_colour] * 64
        letter_padding = [dummy_colour] * 8
        # Build pixels from dictionary
        scroll_pixels = []
        scroll_pixels.extend(string_padding)
        for s in text_string:
            scroll_pixels.extend(
                self._trim_whitespace(self._get_char_pixels(s)))
            scroll_pixels.extend(letter_padding)
        scroll_pixels.extend(string_padding)
        # Recolour pixels as necessary
        coloured_pixels = [
            text_colour if pixel == [255, 255, 255] else back_colour
            for pixel in scroll_pixels
        ]
        # Shift right by 8 pixels per frame to scroll
        scroll_length = len(coloured_pixels) // 8
        for i in range(scroll_length - 8):
            start = i * 8
            end = start + 64
            self.set_pixels(coloured_pixels[start:end])
            time.sleep(scroll_speed)
        self._rotation = previous_rotation

    def show_letter(self,
                    s,
                    text_colour=(255, 255, 255),
                    back_colour=(0, 0, 0)):
        """
        Displays a single text character on the LED matrix using the specified
        colours
        """

        if len(s) > 1:
            raise ValueError(
                'Only one character may be passed into this method')
        # We must rotate the pixel map left through 90 degrees when drawing
        # text, see _load_text_assets
        previous_rotation = self._rotation
        self._rotation -= 90
        if self._rotation < 0:
            self._rotation = 270
        dummy_colour = [None, None, None]
        pixel_list = [dummy_colour] * 8
        pixel_list.extend(self._get_char_pixels(s))
        pixel_list.extend([dummy_colour] * 16)
        coloured_pixels = [
            text_colour if pixel == [255, 255, 255] else back_colour
            for pixel in pixel_list
        ]
        self.set_pixels(coloured_pixels)
        self._rotation = previous_rotation

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

    ####
    # Text assets
    ####

    # Text asset files are rotated right through 90 degrees to allow blocks of
    # 40 contiguous pixels to represent one 5 x 8 character. These are stored
    # in a 8 x 640 pixel png image with characters arranged adjacently
    # Consequently we must rotate the pixel map left through 90 degrees to
    # compensate when drawing text

    def _load_text_assets(self, text_image_file='sense_hat_text.png'):
        """
        Internal. Builds a character indexed dictionary of pixels used by the
        show_message function below
        """
        image_bytes = base64.b64decode(TEXT_IMAGES)
        bytestream = io.BytesIO(image_bytes)
        img = Image.open(bytestream)

        # pylint: disable=bad-builtin
        text_pixels = list(map(list, img.getdata()))

        self._text_dict = {}
        for index, s in enumerate(TEXT_PIXELS):
            start = index * 40
            end = start + 40
            char = text_pixels[start:end]
            self._text_dict[s] = char

    def _trim_whitespace(self, char):  # For loading text assets only
        """
        Internal. Trims white space pixels from the front and back of loaded
        text characters
        """

        psum = lambda x: sum(sum(x, []))
        if psum(char) > 0:
            is_empty = True
            while is_empty:  # From front
                row = char[0:8]
                is_empty = psum(row) == 0
                if is_empty:
                    del char[0:8]
            is_empty = True
            while is_empty:  # From back
                row = char[-8:]
                is_empty = psum(row) == 0
                if is_empty:
                    del char[-8:]
        return char


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

TEXT_PIXELS = (r' +-*/!"#$><0123456789.=)(ABCDEFGHIJKLMNOPQRSTUVWXYZ'
               r"abcdefghijklmnopqrstuvwxyz?,;:|@%[&_']\~")

TEXT_IMAGES = (
    b'iVBORw0KGgoAAAANSUhEUgAAAAgAAAKACAIAAAAuEa5AAAAACXBIWXMAAAsTAAALEwEAmpwY'
    b'AAAAB3RJTUUH3wISDSkNnUO4KwAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeB'
    b'DhcAAAMGSURBVGje7VrJcsMgDDUa/v+X6aGZ2AYtT0iJO1Pp1Jpg7buP40/AGOP6L0m/a+tv'
    b'W2tbr3r04EbrRDHPh59zFQf/22fODGhjjNaawXwMGkurhsN/Q9RHY4Vzvirjxo1K/mC6pOJg'
    b'b1hoILM4n1zPNIp3YwnsHzxJEI+y165of/+m969EPqYzIDIYIgJ07vdfCccxxmDPiGVbE8ks'
    b'vtsxj1/SIEmvpevTmYQJp3YG2O7qOJifa+85qVgJZTiHHKdfxXA1tdkSGUIn5mllzaBKFa2t'
    b'2hsfPK2+HM3Y9fyU/WOvZmBxdJF8P3LWAc90B0nM0BId2bCq6Is1XEZWa/4ywqhL+FdlZbX1'
    b'XKxFd61dxEGivL/gamRUJI7oQ6gFbWVnLIo6LBFAHhY7SebUbZtM0Tn7TquG08SO1qJ91ccv'
    b'DqsCyGh4ARxohOtoVb7bHmgXyaFBI2V2m7jdbtuOuz2D848bA1/AQjMAEQc53HL3qYg84uew'
    b'dCUcHj9PiXBzAenzWnLI/OWDa/sU5JxvFN+RE2oUCc0nWcWEEfo8HUuw+flCkBHjLtkNV3i4'
    b'2Pgxams9MMPUunYoyPTJvAODLfnGam2vxAL1FeKg0amxmZa8uY84CiN2lgCLL9ZBirKSyw9j'
    b'IqtNozRXuyInSM8xzlUf9HSivoDsyecM8gydOwdSmsT8TTVWkX3K2qVpkL9jOezZK+pqh9va'
    b'O1uw7I2881IqI12+sAEGQoEZMhqWPtsoOhk0RqFbWU28QXmVi9/aCaI90c9vWQ3aRqeE1yNh'
    b'qRfvhG3vA26EjcG5xY3n81hiw5pq6OsEYLsUL1gkDcJj9cSO5Y2DdnGg7QosXWjXD1R94XpX'
    b'tU+tHPNITKNKXG0FWhl/YXHro7TeMSY0uD8NfOYDBxZmKyNtLfPxayuhB2BjdI/2MfYKW6zh'
    b'xIW0+qkKO7IQPUrtcVg7V4cDTuluLdx8dmVNINmv4tRNgyMbPLs/fzTguFULLCcTm8b400At'
    b'uptVj4KCgoKCgoKCgoKCgoKCgoKCfwo/4wajTHi9a/gAAAAASUVORK5CYII=')


def main():
    """Simple example."""
    grid = LEDGrid()
    grid.set_pixels(EXAMPLE)
    input()

if __name__ == '__main__':
    main()
