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
FPS = 10
block_size = 20
best_score = 0
font = pygame.font.SysFont('arial', 25)


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
        self.w = w // block_size * block_size
        self.h = h // block_size * block_size
        self.score = 0
        self.food = None
        self.head = Coord(self.w / 2, self.h / 2)
        self.tail = [self.head,
                     Coord(self.head.x - block_size, self.head.y),
                     Coord(self.head.x - (2 * block_size), self.head.y)
                     ]
        self.randomize_food()
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Snake')
        self.clock = pygame.time.Clock()

    def start_game(self):
        """
        Aceasta este functia de start.
            1. In prima parte vom astepta si vom colecta inputul dat de user (apasarile de butoane) si vom trata doar butoanele care ne intereseaza (arrow keys)
            2. In a doua parte vom misca sarpele. Apelam functia snake_move care va plasa urmatoarea pozitie a capului in functie de directia actuala si
                    apoi vom insera pe pozitia 0 din coada noul cap al sarpelui. Dupa asta verificam daca sarpele a prins mancarea si crestem scorul sau
                    in caz contrar vom face pop adica vom scoate ultimul element din coada pentru a asigura principiul de move forward al sarpelui. Dupa
                    toate aceste operatiuni vom face update graficii tablei de joc si la best score in caz ca este nevoie.
            3. In a treia parte vom verifica daca sarpele este intr-o pozitie valida in momentul respectiv. In caz ca nu este, vom actualiza variabila game_over
                    care va face bucla din main sa se opreasca. In caz ca sarpele este intr-o pozitie valida vom continua jocul in mod normal.
        :return: Va returna intotdeauna variabila game_over care va fi destructurata in variabila end_game si va intrerupe bucla din main daca este True,
                    asadar va termina jocul. In caz contrar, jocul va continua in mod normal.
        """
        # 1.
        event = pygame.event.poll()
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_END:
                pygame.quit()
                quit()
            if event.key == pygame.K_LEFT and self.direction != Direction.RIGHT:
                self.direction = Direction.LEFT
            elif event.key == pygame.K_RIGHT and self.direction != Direction.LEFT:
                self.direction = Direction.RIGHT
            elif event.key == pygame.K_UP and self.direction != Direction.DOWN:
                self.direction = Direction.UP
            elif event.key == pygame.K_DOWN and self.direction != Direction.UP:
                self.direction = Direction.DOWN

        # 2.
        self.snake_move(self.direction)
        self.tail.insert(0, self.head)
        if self.head == self.food:
            self.score += 1
            self.randomize_food()
        else:
            self.tail.pop()
        if self.score > self.BEST:
            self.BEST = self.score
        self.render()
        self.clock.tick(FPS)

        # 3.
        game_over = False
        if self.check_if_final_state():
            game_over = True

        return game_over

    def randomize_food(self):
        """
        Aici vom seta coordonatele pentru mancare, care vor fi random si vom verifica sa nu cumva sa se suprapuna cu corpul sarpelui
        Operatia  efectuata la x si y ne va ajuta sa scapam de restul impartirii la variabila block_size ca sa putem incadra mancarea
            fix intr-o casuta de marimea block_size.
        :return: No return.
        """
        x = random.randint(0, (self.w - block_size) // block_size) * block_size
        y = random.randint(0, (self.h - block_size) // block_size) * block_size
        self.food = Coord(x, y)
        if self.food in self.tail:
            self.randomize_food()

    def render(self):
        """
        Aceasta functie va randa in mod constant tot ce vedem in fereastra de joc, pe baza coordonatelor "obiectelor"
            cum ar fi sarpele, ochii sarpelui, mancarea, culoarea plansei de joc.
        :return: No return.
        """
        self.display.fill(background)
        for pt in self.tail:
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
        self.draw_obstacles()
        pygame.draw.ellipse(self.display, RED, pygame.Rect(self.food.x, self.food.y, block_size - 4, block_size - 4))
        text = font.render("Score: " + str(self.score), True, GREEN)
        self.display.blit(text, [0, 0])
        text = font.render("Best: " + str(self.BEST), True, GREEN)
        self.display.blit(text, [0, block_size + 10])
        pygame.display.flip()

    def snake_move(self, direction):
        """
        In aceasta functie calculam noile coordonate ale capului sarpelui si actualizam capul sarpelui.
        :param direction: Directia in care merge sarpele, ne va ajuta sa calculam noile coordonate.
        :return: No return.
        """

        x = self.head.x
        y = self.head.y

        if borderless and self.head.x > self.w - 2 * block_size and self.direction == Direction.RIGHT:
            x = 0
        elif borderless and self.head.x < block_size and self.direction == Direction.LEFT:
            x = self.w - block_size
        elif borderless and self.head.y > self.h - 2 * block_size and self.direction == Direction.DOWN:
            y = 0
        elif borderless and self.head.y < block_size and self.direction == Direction.UP:
            y = self.h - block_size
        elif direction == Direction.RIGHT:
            x += block_size
        elif direction == Direction.LEFT:
            x -= block_size
        elif direction == Direction.DOWN:
            y += block_size
        elif direction == Direction.UP:
            y -= block_size

        self.head = Coord(x, y)

    def check_if_final_state(self):
        """
        Aceasta functie verifica daca jocul se afla in starea finala, adica daca sarpele si-a muscat coada, daca a atins marginea tablei de joc in caz
            ca este dezactivata optionea borderless sau daca acesta a intrat in coliziune cu un obstacol.

        :return: True daca sarpele a facut o miscare gresita, False in caz ca sarpele a facut o mutare corecta.
        """
        if borderless is False and self.head.x > self.w - block_size or self.head.x < 0 or self.head.y > self.h - block_size or self.head.y < 0:
            return True
        if self.head in self.tail[1:]:
            return True
        if self.head in obstacles:
            return True
        return False

    def draw_obstacles(self):
        """
        Aceasta functie va desena pe tabla de joc obstacolele in functie de coordonatele obstacolelor primite de la fisierul de configurare.
        :return: No return.
        """
        for obstacle in obstacles:
            pygame.draw.rect(self.display, BLACK, pygame.Rect(obstacle[0], obstacle[1], block_size, block_size))


if __name__ == '__main__':
    snake = Snake()

    while True:
        end_game = snake.start_game()
        if end_game:
            break

    pygame.quit()
