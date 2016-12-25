#!/usr/bin/python3

"""Greco - Green Code learning game.

By Zeth, 2016

"""

from __future__ import division
from __future__ import print_function

import os
import json
import difflib
from random import choice

# Use SDL2 Pygame if available, SD1 if not.
try:
    import pygame_sdl2
except ImportError:
    SDL = 1
else:
    pygame_sdl2.import_as_pygame()
    SDL = 2

import pygame
# pylint: disable=no-member,no-name-in-module
from pygame.locals import (QUIT, KEYDOWN, K_RETURN, K_PAUSE,
                           K_HELP, K_INSERT, K_ESCAPE)

from ledgrid import LEDGrid, LED
from greencode import GreenCode, WHITE, OFF

try:
    from eztext import Input
except ImportError:
    from .eztext import Input


__version__ = "0.1.2"

STARTING_LEVEL = 0

PAUSE_BUTTONS = (K_PAUSE, K_HELP, K_INSERT, K_ESCAPE)

LETTERS = "etaoinshrdlcumwfgypbvkj0123456789etaoinshrdlcumwfgypbvkjxqz"

TITLE = 'Greco - Green Code Learning Game'


class Game(object):  # pylint: disable=too-many-instance-attributes
    """The main game class."""
    def __init__(self):
        self.finished = 0
        self.paused = False
        self.text_box = None
        self.background = None
        self.clock = None
        self.levels = None
        self.info = {}
        self.frame_count = 0
        self.frame_rate = 60
        self._current_target = 'e'
        self.key = []
        self.fonts = {}
        self.gcode = GreenCode()
        self._setup_game()
        self._setup_ui()
        self.current_target = 'e'
        directory = os.path.split(__file__)[0]
        self._teapot_path = os.path.join(directory, "dotty-tea-pot.png")
        self._sound_path = os.path.join(directory, "sounds")

    def run_game(self):
        """The main game loop."""
        self._welcome()

        while self.finished == 0:
            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:
                    self.finished = 1
                    pygame.quit()  # pylint: disable=no-member
                elif event.type == KEYDOWN:
                    if event.key == K_RETURN:
                        self._mark_user_translation()
                    if event.key in PAUSE_BUTTONS:
                        self._pause()

            self.text_box.update(events)
            self._update_display()

    def _setup_game(self):
        """Load the levels and set the game state."""
        directory = os.path.split(__file__)[0]
        with open(os.path.join(directory, 'levels1.json')) as level_buf:
            self.levels = json.load(level_buf)
        with open(os.path.join(directory, 'levels2.json')) as level_buf:
            self.levels.extend(json.load(level_buf))
        self._setup_info()

    def _setup_ui(self):
        pygame.init()  # pylint: disable=no-member
        pygame.font.init()
        self._setup_fonts()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((700, 405), 0, 32)
        # pylint: disable=too-many-function-args
        background = pygame.Surface(self.screen.get_size())
        self.background = background.convert()
        self.background.fill((0, 51, 25))
        self.grid = LEDGrid(screen=self.screen, margins=(10, 40))
        self._setup_text_entry()
        self.clock = pygame.time.Clock()
        self._setup_key()
        self._update_key()

    def _setup_info(self):
        """Setup the player info dictionary with initial data."""
        self.info = {
            "wpm": [1],
            "level": STARTING_LEVEL,
            "average_wpm": 10,
            "accuracy": [90],
            "key_char": 'e',
        }

    def _setup_fonts(self):
        """Set the font sizes."""
        small = 12 if SDL == 2 else 20
        medium = 30 if SDL == 2 else 50
        key = 60 if SDL == 2 else 100

        self.fonts = {
            "small": pygame.font.Font(None, small),
            "medium": pygame.font.Font(None, medium),
            "key": pygame.font.Font(None, key)
        }

    # pylint: disable=too-many-arguments
    def _write_text(self,
                    text,
                    x_pos,
                    y_pos,
                    font="small",
                    colour=WHITE):
        """Friendly method to write text such as headings, scores etc."""
        font = self.fonts[font]
        text_surface = font.render(text, 1, colour)
        self.screen.blit(text_surface, (x_pos, y_pos))

    def _welcome(self):
        """Welcome screen."""
        self.paused = True
        self.screen.fill(OFF)
        self._draw_top_headings()
        self._update_leds(message="welcome friend")

        self._write_text(
            'Welcome',
            370, 10, "key")
        self._write_text(
            "Learn Green Code in a friendly way!",
            400, 75)
        self._write_text(
            "How To Play",
            370, 95, "medium")
        self._write_text(
            "Read the Green Code and type it in.",
            370, 135)
        self._write_text(
            "Use the Backspace key to delete typos.",
            370, 155)
        self._write_text(
            "Return key to submit your guess.",
            370, 175)
        self._write_text(
            "ESC key to pause the game.",
            370, 195)
        self._write_text(
            "Consistently accurate typing will result in gaining",
            370, 215)
        self._write_text(
            "a level and being rewarded with a silly catchphrase.",
            370, 235)
        self._write_text(
            "Each level will focus on a different character,",
            370, 255)
        self._write_text(
            "which is shown by a helpful key on the far right.",
            370, 275)
        self._write_text(
            "Green Code is a whimsical language so start slowly,",
            370, 310)
        self._write_text(
            "don't take it seriously and don't forget to have fun!",
            370, 330)
        self._write_text(
            "Press Return to join the RGB LED Revolution!",
            370, 360)
        self._do_pause()
        self.screen.fill(OFF)
        self._update_leds()

    def _wrong(self, guess):
        """Show the correct answer."""
        self.paused = True
        self.screen.fill(OFF)
        self._draw_top_headings()

        self._write_text('You wrote:', 370, 15)

        if len(guess) < 8:
            self._write_text(guess, 370, 40, "medium")
        else:
            self._write_text(guess[:8], 370, 40, "medium")
            self._write_text(guess[8:], 370, 80, "medium")

        self._write_text('Correct Answer:', 370, 140)

        if len(self.current_target) < 8:
            self._write_text(self.current_target, 370, 165, "medium")
        else:
            self._write_text(self.current_target[:8], 370, 165, "medium")
            self._write_text(self.current_target[8:], 370, 205, "medium")

        self._draw_leds()
        self._do_pause()

    def _pause(self):
        """Pause the game for a tea break."""
        self.paused = True
        self.screen.fill(OFF)
        self._draw_top_headings()
        self._update_leds(message="paused")
        self._write_text("Paused", 400, 250, "key")
        teapot = pygame.image.load(self._teapot_path)
        self.screen.blit(teapot, (400, 50))
        self._do_pause()
        self._update_leds()

    def _do_pause(self):
        """Wait for the game to be resumed."""
        while self.paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.finished = 1
                    pygame.quit()  # pylint: disable=no-member

                if event.type == KEYDOWN:
                    if event.key == K_RETURN:
                        self._unpause()
                    if event.key in PAUSE_BUTTONS:
                        self._unpause()

            pygame.display.update()
            self.clock.tick(15)

    def _unpause(self):
        """Make the fun continue!"""
        self.paused = False

    def _get_new_target(self):
        """Get a new word for the user to type."""
        self.frame_count = 0
        if self.info['level'] < 59:
            level = self.info['level']
            self.current_target = choice(self.levels[level])
            # At lower levels, reroll if length is greater than 8
            while len(self.current_target) > 8:
                self.current_target = choice(self.levels[level])
            self.current_target = choice(self.levels[level])
        else:
            level = level % 59
            self.current_target = choice(self.levels[level])

    def _setup_text_entry(self):
        """Setup the text entry field."""
        if SDL == 2:
            font = pygame.font.Font(None, 19)
        else:
            font = pygame.font.Font(None, 30)

        self.text_box = Input(
            x=370,
            y=300,
            maxlength=16,
            color=(255, 0, 0),
            prompt='',
            font=font)
        self.text_box.draw(self.screen)

    def _play_sound(self):
        """Play the level change silly noise."""
        level = self.info['level']
        if level > 62:
            level = level % 62
        filename = str(level).zfill(2) + ".ogg"

        pygame.mixer.music.load(os.path.join(self._sound_path, filename))
        pygame.mixer.music.play()

    @property
    def current_target(self):
        """I'm the 'current_target' property."""
        return self._current_target

    @current_target.setter
    def current_target(self, value):
        self._current_target = value
        self._update_leds()

    @current_target.deleter
    def current_target(self):
        del self._current_target

    def _update_leds(self,
                     message=None):
        """Set the LED colours."""
        if not message:
            message = self._current_target
        # Get the message
        grids = self.gcode.parse_message(message)
        grid = grids[0]
        # Display the message
        self.grid.set_pixels(grid)

    def _setup_key(self):
        """Setup the helpful key."""
        for row in range(0, 4):
            led = LED(radius=20,
                      pos=(14, row))
            self.key.append(led)

    def _update_key(self):
        """Update the helpful key."""
        grid = self.gcode.parse_character(self.info["key_char"])
        for index, led in enumerate(self.key):
            if grid[index] == OFF:
                led.lit = False
            else:
                led.clicked(grid[index])
                led.lit = True

    def _draw_top_headings(self):
        """Draw the top headings."""
        # Title
        self._write_text(TITLE, 100, 15, "small")

        # Level
        level = 'Level ' + str(self.info['level'])
        self._write_text(level, 5, 15, "small")

    def _draw_side_info(self):
        """Draw the side headings."""
        # Last words per minute
        self._write_text('Last WPM:', 370, 15)

        # Last words per minute number
        wpm = "%.0f" % self.info['wpm'][-1]
        self._write_text(wpm, 370, 30, "key")

        # Average Words per minute
        self._write_text('Average WPM:', 520, 15)

        # Average words per minute number
        awpm = "%.0f" % (sum(self.info['wpm']) / len(self.info['wpm']))
        self._write_text(awpm, 525, 30, "key")

        # Accuracy
        self._write_text('Accuracy:', 370, 100,)

        # Accuracy percentage
        apc = "%.0f" % self._get_average_accuracy()
        self._write_text(apc + '%', 370, 115, "key")

        # Last character title
        self._write_text('Last char added:', 520, 100)

        # Last character key char
        self._write_text(self.info['key_char'], 560, 115, "key")

        # Time
        self._write_text('Time:', 370, 185)

        # Your Guess
        self._write_text('Your input:', 370, 275)

    def _draw_text_box(self):
        """Draw the text input box."""
        self.text_box.draw(self.screen)

    def _set_words_per_minute(self, words=1):
        """Update words per minute."""
        seconds = self.frame_count / self.frame_rate
        wpm = round((60 / seconds) * words)
        self.info['wpm'].append(wpm)

    def _draw_clock(self):
        """Draw how much time the current reading has taken."""
        total_seconds = self.frame_count // self.frame_rate

        # Divide by 60 to get total minutes
        minutes = total_seconds // 60

        # Use modulus (remainder) to get seconds
        seconds = total_seconds % 60

        # Use python string formatting to format in leading zeros
        output_string = "{0:02}:{1:02}".format(minutes, seconds)

        # Blit to the screen
        self._write_text(output_string, 370, 200, "key")
        self.frame_count += 1
        self.clock.tick(self.frame_rate)

    def _draw_leds(self, leds=None):
        """Draw the LEDS."""
        if not leds:
            # pylint: disable=protected-access
            leds = self.grid._draw_leds()
        else:
            for led in leds:
                led.draw()

    def _draw_key(self):
        """Draw the key for the last character added."""
        for led in self.key:
            led.draw()

    def _update_display(self):
        """Update the display while the game is running."""
        self.screen.blit(self.background, (0, 0))
        # draw the leds
        self._draw_leds()
        self._draw_key()
        self._draw_top_headings()
        self._draw_side_info()
        self._draw_text_box()
        self._draw_clock()
        pygame.display.flip()

    def _get_average_accuracy(self):
        """Get the accuracy from the last ten guesses."""
        if len(self.info['accuracy']) < 10:
            length = len(self.info['accuracy'])
        else:
            length = 10

        return round(sum(self.info['accuracy'][-10:]) / length)

    def _upgrade_level(self):
        self.info['accuracy'] = [self._get_average_accuracy()]
        self.info['level'] += 1
        if self.info['level'] < 59:
            self.info["key_char"] = LETTERS[self.info['level']]

        self._update_key()
        self._draw_key()
        pygame.display.flip()
        self._play_sound()

    def _mark_user_translation(self):
        """Update the user's guess."""
        if self.current_target == self.text_box.value:
            self.info['accuracy'].append(100)
        else:
            accuracy = round(difflib.SequenceMatcher(
                a='e', b='house').ratio() * 100)
            self.info['accuracy'].append(accuracy)
            self._wrong(self.text_box.value)
        self.text_box.value = ""
        self._set_words_per_minute()
        if len(self.info['accuracy']) > 10 \
           and self._get_average_accuracy() > 89:
            self._upgrade_level()
        self._get_new_target()


def main():
    """Run the game when the module is executed."""
    game = Game()
    game.run_game()

if __name__ == '__main__':
    main()
