#!/usr/bin/python3
"""Green code reading game.
By Zeth, 2016

Many thanks to Richard Hayler.
The LED, graphics, etc are based on 8x8GridDraw
https://github.com/topshed/RPi_8x8GridDraw
http://richardhayler.blogspot.co.uk/2015/06/creating-images-for-astro-pi-hat.html

"""

import pygame
from pygame.locals import QUIT  # pylint: disable=no-name-in-module
import eztext

WHITE = (255, 255, 255)


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
        self.text_box = None
        self.background = None
        self.clock = None
        self.info = {}
        self.frame_count = 0
        self.frame_rate = 60
        self.leds = []
        self.key = []

        self.setup()
        self.run_game()

    def setup(self):
        """Setup pygame and call other setup commands."""
        self.setup_info()
        pygame.init()  # pylint: disable=no-member
        pygame.font.init()
        pygame.display.set_caption('Green Code Reading Test')
        self.screen = pygame.display.set_mode((700, 395), 0, 32)
        # pylint: disable=too-many-function-args
        background = pygame.Surface(self.screen.get_size())
        self.background = background.convert()
        self.background.fill((0, 51, 25))
        self.setup_text_entry()
        self.clock = pygame.time.Clock()
        self.setup_leds()
        self.setup_key()

    def setup_info(self):
        """Setup the player info dictionary with initial data."""
        self.info = {
            "level": 1,
            "last_wpm": 10,
            "average_wpm": 10,
            "accuracy": 90,
            "key_char": 'e'
        }

    def setup_text_entry(self):
        """Setup the text entry field."""
        self.text_box = eztext.Input(
            x=375,
            y=300,
            maxlength=16,
            color=(255, 0, 0),
            prompt='')
        self.text_box.draw(self.screen)

    def setup_leds(self):
        """Setup the virtual LEDs on the screen."""
        for rank in range(0, 8):
            for row in range(0, 8):
                led = LED(radius=20,
                          pos=(rank, row))
                self.leds.append(led)

    def setup_key(self):
        """Setup the helpful key."""
        for row in range(0, 4):
            led = LED(radius=20,
                      pos=(14, row))
            self.key.append(led)

    def run_game(self):
        """The main game loop."""
        while self.finished == 0:
            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:
                    self.finished = 1
                    pygame.quit()  # pylint: disable=no-member

            self.text_box.update(events)

            self.update_display()

    def draw_headings(self):
        """Draw the help and other headings."""
        small_font = pygame.font.Font(None, 20)
        key_font = pygame.font.Font(None, 100)
        # Title
        text = small_font.render('Green Code Reading Test', 1, WHITE)
        self.screen.blit(text, (150, 15))

        # Level
        text = small_font.render('Level ' + str(self.info['level']), 1, WHITE)
        self.screen.blit(text, (5, 15))

        # Last Words per minute
        text = small_font.render('Last WPM:', 1, WHITE)
        self.screen.blit(text, (400, 15))

        # Last words per minute number
        text = key_font.render(str(self.info['last_wpm']), 1, WHITE)
        self.screen.blit(text, (400, 30))

        # Average Words per minute
        text = small_font.render('Average WPM:', 1, WHITE)
        self.screen.blit(text, (520, 15))

        # Average words per minute number
        text = key_font.render(str(self.info['average_wpm']), 1, WHITE)
        self.screen.blit(text, (525, 30))

        # Accuracy
        text = small_font.render('Accuracy:', 1, WHITE)
        self.screen.blit(text, (400, 100))

        # Accuracy percentage
        text = key_font.render(str(self.info['accuracy']) + '%', 1, WHITE)
        self.screen.blit(text, (400, 115))

        # Last character title
        text = small_font.render('Last char added:', 1, WHITE)
        self.screen.blit(text, (520, 100))

        # Last character key char
        text = key_font.render(self.info['key_char'], 1, WHITE)
        self.screen.blit(text, (560, 115))

        # Time
        text = small_font.render('Time:', 1, WHITE)
        self.screen.blit(text, (400, 185))

    def draw_text_box(self):
        """Draw the text input box."""
        self.text_box.draw(self.screen)

    def draw_clock(self):
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
        self.screen.blit(text, [400, 200])
        self.frame_count += 1
        self.clock.tick(self.frame_rate)

    def draw_leds(self):
        """Draw the LEDS."""
        for led in self.leds:
            led.draw()

    def draw_key(self):
        """Draw the key for the last character added."""
        for led in self.key:
            led.draw()

    def update_display(self):
        """Update the display while the game is running."""
        self.screen.blit(self.background, (0, 0))
        # draw the leds
        self.draw_leds()
        self.draw_key()
        self.draw_headings()
        self.draw_text_box()
        self.draw_clock()
        pygame.display.flip()


def main():
    """Run the game when the module is executed."""
    Game()

if __name__ == '__main__':
    main()
