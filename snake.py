import json
import sys
from collections import namedtuple
import enum
import random

import pygame

pygame.init()

Coord = namedtuple('Coord', 'x, y')


class Direction(enum.Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4


# ---------------------------------------- JSON DATA UNPACKING ---------------------------------------------

"""
    JSON Unpacking:
    Am folosit modulul json pentru a face load la stringul din fisierul de config si pentru a-l transforma intr-un dictionar.
    Am folosit modulul sys pentru a lua datele argumentului argv[1] de la linia de comanda, adica fisierul json.
    La final am salvat toate datele din fisierul de config in niste variabile pentru a manevra mai usor datele.
"""


def unpack_json():
    with open(sys.argv[1], 'r') as f:
        contents = f.read()
    cfg = json.loads(contents)
    return cfg


config = unpack_json()
borderless = config['borderless']
obstacles = [tuple(x) for x in config['obstacles']]
width = config['table_size'][0]
height = config['table_size'][1]

# print("Borderless:", borderless)
# print("Obstacles:", obstacles)
# print("Width:", width)
# print("Height:", height)

# -------------------------------------------- VARIABILE GENERALE ---------------------------------------------------

background = (240, 243, 189)
WHITE = (255, 255, 255)
RED = (220, 0, 0)
GREEN = (33, 77, 34)
BRIGHT_GREEN = (47, 111, 55)
CENTER_GREEN = (16, 66, 22)
YELLOW = (139, 69, 19)
BRIGHT_YELLOW = (160, 82, 45)
BRIGHT_YELLOW2 = (205, 133, 63)
BLACK = (0, 0, 0)
block_size = 20
best_score = 0


# -------------------------------------------- IMPLEMENTARE GUI JOC -------------------------------------------------


class Snake:
    BEST = 0

    def __init__(self, w=width, h=height):
        """
        In constructor am initial starea initiala a jocului, cum ar fi scorul, mancarea de pe harta,
        primele 3 componente ale sarpelui (capul si 2 blocuri de corp) si am pornit fereastra de joc.
        :param w: seteaza latimea ferestrei de joc care va fi egala cu variabila preluata din fisierul de config
        :param h: seteaza inaltimea ferestrei de joc care va fi egala cu variabila preluata din fisierul de config
        """
        self.direction = Direction.RIGHT
        self.w = w
        self.h = h
        self.score = 0
        self.food = None
        self.head = Coord(self.w / 2, self.h / 2)
        self.body = [self.head,
                     Coord(self.head.x - block_size, self.head.y),
                     Coord(self.head.x - (2 * block_size), self.head.y)
                     ]
        self.randomize_food()
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Snake')
        self.clock = pygame.time.Clock()

    def start_game(self):
        """Apelam functia care face update la GUI-ul jocului"""
        self.render()

    def randomize_food(self):
        """
        Aici vom seta coordonatele pentru mancare, care vor fi random si vom verifica sa nu cumva sa se suprapuna cu corpul sarpelui
        Operatia  efectuata la x si y ne va ajuta sa scapam de restul impartirii la variabila block_size ca sa putem incadra mancarea
            fix intr-o casuta de marimea block_size.
        """
        x = random.randint(0, (self.w - block_size) // block_size) * block_size
        y = random.randint(0, (self.h - block_size) // block_size) * block_size
        self.food = Coord(x, y)
        if self.food in self.body:
            self.randomize_food()

    def render(self):
        """
        Aceasta functie va randa in mod constant tot ce vedem in fereastra de joc, pe baza coordonatelor "obiectelor"
            cum ar fi sarpele, ochii sarpelui, mancarea, culoarea plansei de joc.
        """
        self.display.fill(background)
        for pt in self.body:
            pygame.draw.ellipse(self.display, GREEN, pygame.Rect(pt.x, pt.y, block_size, block_size))
            if pt == self.head:
                if self.direction == Direction.RIGHT:
                    pygame.draw.ellipse(self.display, WHITE, pygame.Rect(pt.x + 10, pt.y + 4, 4, 4))
                    pygame.draw.ellipse(self.display, WHITE, pygame.Rect(pt.x + 10, pt.y + 12, 4, 4))
                    pygame.draw.ellipse(self.display, BLACK, pygame.Rect(pt.x + 12, pt.y + 5, 2, 2))
                    pygame.draw.ellipse(self.display, BLACK, pygame.Rect(pt.x + 12, pt.y + 13, 2, 2))
                elif self.direction == Direction.LEFT:
                    pygame.draw.ellipse(self.display, WHITE, pygame.Rect(pt.x + 5, pt.y + 4, 4, 4))
                    pygame.draw.ellipse(self.display, WHITE, pygame.Rect(pt.x + 5, pt.y + 12, 4, 4))
                    pygame.draw.ellipse(self.display, BLACK, pygame.Rect(pt.x + 5, pt.y + 5, 2, 2))
                    pygame.draw.ellipse(self.display, BLACK, pygame.Rect(pt.x + 5, pt.y + 13, 2, 2))
                elif self.direction == Direction.DOWN:
                    pygame.draw.ellipse(self.display, WHITE, pygame.Rect(pt.x + 4, pt.y + 10, 4, 4))
                    pygame.draw.ellipse(self.display, WHITE, pygame.Rect(pt.x + 12, pt.y + 10, 4, 4))
                    pygame.draw.ellipse(self.display, BLACK, pygame.Rect(pt.x + 5, pt.y + 12, 2, 2))
                    pygame.draw.ellipse(self.display, BLACK, pygame.Rect(pt.x + 13, pt.y + 12, 2, 2))
                elif self.direction == Direction.UP:
                    pygame.draw.ellipse(self.display, WHITE, pygame.Rect(pt.x + 4, pt.y + 5, 4, 4))
                    pygame.draw.ellipse(self.display, WHITE, pygame.Rect(pt.x + 12, pt.y + 5, 4, 4))
                    pygame.draw.ellipse(self.display, BLACK, pygame.Rect(pt.x + 5, pt.y + 5, 2, 2))
                    pygame.draw.ellipse(self.display, BLACK, pygame.Rect(pt.x + 13, pt.y + 5, 2, 2))
            else:
                pygame.draw.ellipse(self.display, BRIGHT_GREEN, pygame.Rect(pt.x + 2, pt.y + 2, 16, 16))
                pygame.draw.ellipse(self.display, CENTER_GREEN, pygame.Rect(pt.x + 6, pt.y + 6, 8, 8))

        pygame.draw.ellipse(self.display, RED, pygame.Rect(self.food.x, self.food.y, block_size - 4, block_size - 4))
        pygame.display.flip()


if __name__ == '__main__':
    snake = Snake()
    while True:
        snake.start_game()
    # pygame.quit()
