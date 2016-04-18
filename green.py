#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Vertical letter code.

Includes all of ISO/IEC 8859-1
Except for the following missing chars:  ¢¥¤§¦©¨«ª­¬¯®±°³²µ´·¶¹¸»º½¼¾×÷
"""

from itertools import permutations
from string import ascii_lowercase, digits

try:
    from sense_hat import SenseHat
except ImportError:
    SENSE_HAT_LIB = False
else:
    SENSE_HAT_LIB = True


def make_combinations(char):
    """Make all combinations of a set"""
    return {char + ''.join(combi).split(' ', 1)[0].ljust(2)
            for combi in permutations('...---    ', 2)}

RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
PURPLE = (102, 0, 204)
PINK = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
OFF = (0, 0, 0)

BLANK = '    '

COLOURS = (
    (' ', OFF),      # Off
    ('.', BLUE),    # Dark
    ('-', RED),     # Light
    ('#', GREEN),   # Numbers
    ('&', YELLOW),  # Punctuation
    ('^', PURPLE),  # Symbols
    (';', ORANGE),  # European letters
    ('=', CYAN)     # European letters
)

LETTERS = (
    '.-  ',  # a
    '-...',  # b
    '-.-.',  # c
    '-.. ',  # d
    '.   ',  # e
    '..-.',  # f
    '--. ',  # g
    '....',  # h
    '..  ',  # i
    '.---',  # j
    '-.- ',  # k
    '.-..',  # l
    '--  ',  # m
    '-.  ',  # n
    '--- ',  # o
    '.--.',  # p
    '--.-',  # q
    '.-. ',  # r
    '... ',  # s
    '-   ',  # t
    '..- ',  # u
    '...-',  # v
    '.-- ',  # w
    '-..-',  # x
    '-.--',  # y
    '--..'   # z
)

NUMBERS = (
    '#   ',  # 0
    '#.  ',  # 1
    '#.. ',  # 2
    '#...',  # 3
    '#.- ',  # 4 i.e. IV
    '#-  ',  # 5 i.e. V
    '#-. ',  # 6 i.e. VI
    '#-..',  # 7 i.e. VII
    '#..-',  # 8 - Imagine it is  #..-- i.e. IIVV
    '#.--',  # 9 i.e. IVV
)

SYMBOLS = (
    ('\n', '._._'),  # New line/full stop
    (' ', '    '),  # Space
    (',', '----'),  # Comma
    ('?', '..--'),  # Question Mark
    ('!', '---.'),  # Exclamation Mark
    ('+', '#--.'),  # Plus/Add
    ('-', '#-- '),  # Hypen/minus
    ('=', '#---'),  # Equals
    ('/', '#.-.'),  # Slash or divide i.e dot line dot: ÷
    ('*', '#-.-'),  # Asterisk/multiply
    ('.', '&   '),  # Full stop/period
    ('%', '&.-.'),  # Percent
    ("'", '&-  '),  # Single Quote/Apostrophe
    ('"', '&-- '),  # Double Quote
    (':', '&.. '),  # Colon
    (';', '&.- '),  # Semi Colon
    ('@', '&.--'),  # At Sign
    ('(', '&---'),  # Open Parenthesis
    (')', '&--.'),  # Close Parenthesis
    ('_', '&-. '),  # Underscore
    ('$', '&-.-'),  # Dollar sign
    ('>', '&-..'),  # Greater than
    ('#', '&.  '),  # Number sign/Hash
    ('<', '&..-'),  # Less than
    ('&', '&...'),  # Ampersand
    ('\\', '^.-.'),  # Back Slash
    ('^', '^   '),  # Caret
    ('`', '^-  '),  # Grave accent/backtick
    ('|', '^-- '),  # Vertical bar
    ('~', '^-. '),  # Tilde
    ('{', '^-.-'),  # Open brace/curly bracket
    ('}', '^-..'),  # Close brace/curly bracket
    ('[', '^.  '),  # Open Square brackets
    (']', '^.. '),  # Close Square brackets
    ('£', '^--.'),  # Pound Sign
    ('€', '^.--'),  # Euro sign
)

EUROPEAN = (
    ('ß', '^...'),  # sharp s
    ('ä', '^.- '),  # a with diaeresis
    ('ö', '^---'),  # o with diaeresis
    ('ü', '^..-'),  # u with diaeresis
    ('ï', ';-- '),  # i with diaeresis
    ('ë', ';-. '),  # e with diaeresis
    ('ÿ', ';---'),  # y with diaeresis
    ('é', ';.  '),  # e with acute accent
    ('à', ';.- '),  # a with grave accent
    ('è', ';.. '),  # e with grave accent
    ('ù', ';..-'),  # u with grave accent
    ('â', ';.--'),  # a with circumflex
    ('ê', ';...'),  # e with circumflex
    ('î', ';-..'),  # i with circumflex
    ('ô', ';--.'),  # o with circumflex
    ('û', ';-  '),  # u with circumflex
    ('ç', ';-.-'),  # c with cedilla
    ('í', ';.-.'),  # i with acute accent
    ('ú', ';   '),  # u with acute accent
    ('ó', '=...'),  # o with acute accent
    ('á', '=.- '),  # a with acute accent
    ('å', '=-.-'),  # a with ring
    ('ñ', '=-. '),  # n with virgulilla
    ('ã', '=.. '),  # a with virgulilla
    ('õ', '=---'),  # o with virgulilla
    ('¿', '=..-'),  # Inverted question mark
    ('¡', '=--.'),  # Inverted exclamation point
    ('ø', '=-- '),  # o with stroke
    ('ý', '=-..'),  # y with acute accent
    ('ò', '=.  '),  # o with grave accent
    ('ì', '=.-.'),  # i with grave accesnt
    ('æ', '=-  '),  # ash (ae ligature)
    ('ð', '=.--'),  # eth
    ('þ', '=   '),  # thorn
)


def chunk_string(string, length):
    """Chunk string into length long chunks."""
    return [string[0+i:length+i] for i in range(0, len(string), length)]


class GreenCode(object):
    """Green code text representation.
    At the moment we only support Sense HAT,
    support for Unicorn pHAT and virtual pygame
    display may come later.
    """
    def __init__(self,
                 hat='sense'):
        self.characters = dict(zip(ascii_lowercase, LETTERS))
        self.characters.update(zip(digits, NUMBERS))
        self.characters.update(SYMBOLS)
        self.characters.update(EUROPEAN)
        self.colours = dict(COLOURS)
        if hat == 'sense' and SENSE_HAT_LIB:
            self.hat_type = 'sense'
            self.hat = SenseHat()
        else:
            self.hat_type = None
        self.blankpart = [OFF for i in range(0, 32)]

    def show_message(self, message):
        """Show a message on the relevant LED grid."""
        screens = self.split_message(message.lower())
        grids = [self.convert_screen_to_matrix(screen) for screen in screens]
        if self.hat_type == 'sense':
            for grid in grids:
                # Support the joystick later
                self.hat.set_pixels(grid)
                input()

    def split_message(self, message):
        """Split a message into screen sized amounts."""
        screens = []
        last_screen_length = 0
        carry_over_space = False
        for word in message.split():
            if carry_over_space:
                word = ' ' + word
                carry_over_space = False
            if len(word) < 8:
                if last_screen_length == 1:
                    screens[-1].append(word)
                    last_screen_length = 2
                else:
                    screens.append([word, ])
                    last_screen_length = 1
            else:
                chunks = chunk_string(word, 8)
                if len(chunks[-1]) == 8:
                    carry_over_space = True
                if last_screen_length == 1:
                    screens[-1].append(chunks.pop(0))
                    if not chunks:
                        last_screen_length = 2
                        continue
                while len(chunks) > 2:
                    screens.append([chunks.pop(0),
                                    chunks.pop(0)])

                last_screen_length = len(chunks)
                screens.append(chunks)
        return screens

    def convert_screen_to_matrix(self, screen):
        """Convert screen of text to matrix that the HAT
        library understands."""
        grid = []
        for word in screen:
            part = []
            for letter in word:
                try:
                    part.append(self.characters[letter])
                except KeyError:
                    part.append(BLANK)
            while len(part) < 8:
                part.append(BLANK)
            for row in range(0, 4):
                for column in range(0, 8):
                    grid.append(self.colours[part[column][row]])
        if len(screen) == 1:
            grid.extend(self.blankpart)
        return grid


def example():
    """A simple example."""
    gcode = GreenCode()
    gcode.show_message("hello world")

if __name__ == "__main__":
    example()
