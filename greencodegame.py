#!/usr/bin/python3
"""Green code reading game.
By Zeth, 2016

Many thanks to Richard Hayler.
The LED class, graphics, etc are based on 8x8GridDraw
https://github.com/topshed/RPi_8x8GridDraw
http://richardhayler.blogspot.co.uk/2015/06/creating-images-for-astro-pi-hat.html

"""

import json
import difflib
from random import choice, randint
import pygame
# pylint: disable=no-member,no-name-in-module
from pygame.locals import (QUIT, KEYDOWN, K_RETURN, K_PAUSE,
                           K_HELP, K_INSERT, K_ESCAPE)
from eztext import Input
from green import GreenCode, WHITE, OFF

STARTING_LEVEL = 0

PAUSE_BUTTONS = (K_PAUSE, K_HELP, K_INSERT, K_ESCAPE)

LETTERS = "etaoinshrdlcumwfgypbvkj0123456789etaoinshrdlcumwfgypbvkjxqz"


class LED(object):
    """A virtual LED, shown using pygame."""
    def __init__(self, pos=(0, 0), radius=25, lit=False):
        # Initializes the LED
        self.pos = pos
        self.lit = lit
        self.radius = radius
        self.screen = pygame.display.get_surface()
        self.color = WHITE
        self.pos_x = int(self.pos[0] * (self.radius * 2 + 5)) + (self.radius)
        self.pos_y = int(self.pos[1] * (self.radius *
                                        2 + 5)) + (self.radius) + 40

    def draw(self):
        """Draws the LED."""
        # Draws a circle
        if self.lit:  # has it been clicked?
            thickness = 0
        else:
            self.color = [255, 255, 255]
            thickness = 1

        pygame.draw.circle(
            self.screen,
            self.color,
            (self.pos_x, self.pos_y),
            self.radius, thickness)

        # Draws a square
        pygame.draw.rect(
            self.screen,
            self.color,
            (self.pos_x - self.radius,
             self.pos_y - self.radius,
             (2 * self.radius),
             (2 * self.radius)),
            thickness)

    def clicked(self, colour):
        """What to do when clicked, note we don't need this."""
        self.color = colour
        if self.lit:
            self.lit = False
        else:
            self.lit = True


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
        self.leds = []
        self.key = []
        self.fonts = {}
        self.gcode = GreenCode(hat=None)
        self._setup()
        self.current_target = 'e'

    def run_game(self):
        """The main game loop."""
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
            self.update_display()

    def _setup(self):
        """Setup pygame and call other setup commands."""
        with open('levels1.json') as level_buf:
            self.levels = json.load(level_buf)
        with open('levels2.json') as level_buf:
            self.levels.extend(json.load(level_buf))
        self._setup_info()
        pygame.init()  # pylint: disable=no-member
        pygame.font.init()
        self._setup_fonts()
        pygame.display.set_caption('Green Code Reading Test')
        self.screen = pygame.display.set_mode((700, 395), 0, 32)
        # pylint: disable=too-many-function-args
        background = pygame.Surface(self.screen.get_size())
        self.background = background.convert()
        self.background.fill((0, 51, 25))
        self._setup_text_entry()
        self.clock = pygame.time.Clock()
        self._setup_leds()
        self.setup_key()
        self.update_key()

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
        self.fonts = {
            "small": pygame.font.Font(None, 20),
            "medium": pygame.font.Font(None, 50),
            "key": pygame.font.Font(None, 100)
        }

    def _wrong(self, guess):
        """Show the correct answer."""
        self.paused = True
        self.screen.fill(OFF)
        self._draw_top_headings()
        small_font = self.fonts["small"]
        medium_font = self.fonts["medium"]

        text = small_font.render('You wrote:', 1, WHITE)
        self.screen.blit(text, (370, 15))

        if len(guess) < 8:
            text = medium_font.render(guess, 1, WHITE)
            self.screen.blit(text, (370, 40))
        else:
            text = medium_font.render(guess[:8], 1, WHITE)
            self.screen.blit(text, (370, 40))
            text = medium_font.render(guess[8:], 1, WHITE)
            self.screen.blit(text, (370, 80))

        text = small_font.render('Correct Answer:', 1, WHITE)
        self.screen.blit(text, (370, 140))

        if len(self.current_target) < 8:
            text = medium_font.render(self.current_target, 1, WHITE)
            self.screen.blit(text, (370, 165))
        else:
            text = medium_font.render(self.current_target[:8], 1, WHITE)
            self.screen.blit(text, (370, 165))
            text = medium_font.render(self.current_target[8:], 1, WHITE)
            self.screen.blit(text, (370, 205))

        self._draw_leds()
        self._do_pause()

    def _pause(self):
        """Pause the game for a tea break."""
        self.paused = True
        self.screen.fill(OFF)
        self._draw_top_headings()
        key_font = self.fonts["key"]

        text = key_font.render("Paused", 1, WHITE)
        self.screen.blit(text, (400, 250))

        teapot = pygame.image.load("dotty-tea-pot.png")
        self.screen.blit(teapot, (400, 50))

        leds = []
        self._setup_leds(leds)
        self.update_leds(message="paused",
                         leds=leds)
        self._draw_leds(leds)
        self._do_pause()

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
            level = randint(0, 25)
            self.current_target = choice(self.levels[level])

    def _setup_text_entry(self):
        """Setup the text entry field."""
        self.text_box = Input(
            x=360,
            y=300,
            maxlength=16,
            color=(255, 0, 0),
            prompt='')
        self.text_box.draw(self.screen)

    def _setup_leds(self, leds=None):
        """Setup the virtual LEDs on the screen."""
        if not leds:
            leds = self.leds
        for rank in range(0, 8):
            for row in range(0, 8):
                led = LED(radius=20,
                          pos=(rank, row))
                leds.append(led)

    def _play_sound(self):
        """Play the level change silly noise."""
        level = self.info['level']

        filename = "sounds/" + str(level).zfill(2) + ".ogg"

        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

    @property
    def current_target(self):
        """I'm the 'current_target' property."""
        return self._current_target

    @current_target.setter
    def current_target(self, value):
        self._current_target = value
        self.update_leds()

    @current_target.deleter
    def current_target(self):
        del self._current_target

    def update_leds(self,
                    message=None,
                    leds=None):
        """Set the LED colours."""
        if not message:
            message = self._current_target
        if not leds:
            leds = self.leds
        # Reset first
        for led in leds:
            led.lit = False
        # Get the message
        grids = self.gcode.parse_message(message)
        grid = grids[0]
        # Display the message
        for led in leds:
            rotated = (led.pos[1] * 8) + led.pos[0]
            if grid[rotated] == OFF:
                led.lit = False
            else:
                led.clicked(grid[rotated])

    def setup_key(self):
        """Setup the helpful key."""
        for row in range(0, 4):
            led = LED(radius=20,
                      pos=(14, row))
            self.key.append(led)

    def update_key(self):
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
        small_font = self.fonts["small"]

        # Title
        text = small_font.render('Green Code Reading Test', 1, WHITE)
        self.screen.blit(text, (150, 15))

        # Level
        text = small_font.render('Level ' + str(self.info['level']), 1, WHITE)
        self.screen.blit(text, (5, 15))

    def _draw_side_info(self):
        """Draw the side headings."""
        small_font = self.fonts["small"]
        key_font = self.fonts["key"]

        # Last Words per minute
        text = small_font.render('Last WPM:', 1, WHITE)
        self.screen.blit(text, (370, 15))

        # Last words per minute number
        text = key_font.render(str(self.info['wpm'][-1]), 1, WHITE)
        self.screen.blit(text, (370, 30))

        # Average Words per minute
        text = small_font.render('Average WPM:', 1, WHITE)
        self.screen.blit(text, (520, 15))

        # Average words per minute number
        text = key_font.render(str(round(sum(
            self.info['wpm']) / len(self.info['wpm']))), 1, WHITE)
        self.screen.blit(text, (525, 30))

        # Accuracy
        text = small_font.render('Accuracy:', 1, WHITE)
        self.screen.blit(text, (370, 100))

        # Accuracy percentage
        text = key_font.render(str(
            self._get_average_accuracy()) + '%', 1, WHITE)
        self.screen.blit(text, (370, 115))

        # Last character title
        text = small_font.render('Last char added:', 1, WHITE)
        self.screen.blit(text, (520, 100))

        # Last character key char
        text = key_font.render(self.info['key_char'], 1, WHITE)
        self.screen.blit(text, (560, 115))

        # Time
        text = small_font.render('Time:', 1, WHITE)
        self.screen.blit(text, (370, 185))

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
        font = pygame.font.Font(None, 100)
        text = font.render(output_string, True, WHITE)
        self.screen.blit(text, [370, 200])
        self.frame_count += 1
        self.clock.tick(self.frame_rate)

    def _draw_leds(self, leds=None):
        """Draw the LEDS."""
        if not leds:
            leds = self.leds
        for led in leds:
            led.draw()

    def _draw_key(self):
        """Draw the key for the last character added."""
        for led in self.key:
            led.draw()

    def update_display(self):
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

        self.update_key()
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
