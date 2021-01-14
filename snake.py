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
obstacles_number = config['obstacles_number']
borderless = config['borderless']
fixed = config['fixed_obstacle']
obstacles = [tuple(x) for x in config['obstacles']]
width = config['table_size'][0]
height = config['table_size'][1]
FPS = config['fps']

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
font = pygame.font.SysFont('arial', 25)
clicked = False


# -------------------------------------------- IMPLEMENTARE GUI JOC -------------------------------------------------


class Snake:
    BEST = 0

    def __init__(self, w=width, h=height, fps=FPS):
        """
        In constructor am initial starea initiala a jocului, cum ar fi scorul, mancarea de pe harta,
        primele 3 componente ale sarpelui (capul si 2 blocuri de corp) si am pornit fereastra de joc.
        :param w: seteaza latimea ferestrei de joc care va fi egala cu variabila preluata din fisierul de config
        :param h: seteaza inaltimea ferestrei de joc care va fi egala cu variabila preluata din fisierul de config
        """
        self.direction = Direction.RIGHT
        self.w = w // block_size * block_size
        self.h = h // block_size * block_size
        self.difficulty = fps
        self.score = 0
        self.obstacles_drawn = 0
        self.food = None
        self.obstacles = []
        self.difficulty_increased = 0
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
            self.difficulty_increased = 0
        else:
            self.tail.pop()
        if self.score > self.BEST:
            self.BEST = self.score
        self.increase_difficulty()
        self.render()
        self.clock.tick(self.difficulty)

        # 3.
        game_over = False
        if self.check_if_final_state():
            game_over = True

        if game_over:

            if PlayAgain(self.score, self.BEST).play_again():
                game_over = False
                self.direction = Direction.RIGHT
                self.head = Coord(self.w / 2, self.h / 2)
                self.tail = [self.head,
                             Coord(self.head.x - block_size, self.head.y),
                             Coord(self.head.x - (2 * block_size), self.head.y)]
                self.score = 0
                self.obstacles = []
                self.obstacles_drawn = 0
                self.food = None
                self.randomize_food()

        return game_over, self.BEST

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
        if self.food in self.tail or self.food in obstacles:
            self.randomize_food()

    def randomize_obstacles(self):
        """
        Aici se vor genera obstacole random in functie de un numar de obstacole primit de la tastatura.
        :return:
        """
        x = random.randint(0, (self.w - block_size) // block_size) * block_size
        y = random.randint(0, (self.h - block_size) // block_size) * block_size
        tmp_obstacle = Coord(x, y)
        if tmp_obstacle in self.tail or (tmp_obstacle.y == self.head.y and tmp_obstacle.x - self.head.x == 4*block_size):
            self.randomize_obstacles()
        else:
            self.obstacles.append(tmp_obstacle)

    def save_obstacles(self):
        if self.obstacles_drawn == 0:
            for i in range(obstacles_number):
                self.randomize_obstacles()
        self.obstacles_drawn = 1

    def increase_difficulty(self):
        if self.score % 5 == 0 and self.score != 0 and self.difficulty_increased == 0:
            self.difficulty += 5
            self.difficulty_increased = 1

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
        if fixed:
            if self.head in obstacles:
                return True
        else:
            if self.head in self.obstacles:
                return True
        return False

    def draw_obstacles(self):
        """
        Aceasta functie va desena pe tabla de joc obstacolele in functie de datele obstacolelor primite de la fisierul de configurare.
        :return: No return.
        """
        if fixed:
            for obstacle in obstacles:
                pygame.draw.rect(self.display, BLACK, pygame.Rect(obstacle[0], obstacle[1], block_size, block_size))
        else:
            self.save_obstacles()
            for obstacle in self.obstacles:
                pygame.draw.rect(self.display, BLACK, pygame.Rect(obstacle[0], obstacle[1], block_size, block_size))


def display_best_score():
    """
    Aceasta functie va afisa fereastra finala, cand jucatorul decide sa paraseasca jocul si va apasa "quit game". In aceasta fereastra va fi afisat cel
        mai mare scor. Pentru a iesi de tot din joc va mai trebui apasata pentru ultima oara o tasta la intamplare.
    :return: No return.
    """
    while True:
        display = pygame.display.set_mode((width, height))
        pygame.display.set_caption('Snake')
        display.fill(background)
        text = font.render("Congrats! Your Best Score is: " + str(best_score), True, GREEN)
        text2 = font.render("Press any key to exit the game", True, GREEN)
        display.blit(text, [width / 4 + 20, height / 2 - 50])
        display.blit(text2, [width / 3 - 40, height - 100])
        pygame.display.flip()
        event = pygame.event.poll()
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
            pygame.quit()
            quit()


class PlayAgain:
    play = False
    exit = False

    def __init__(self, final_score, best_scoree, w=width, h=height):
        """
        In constructor vom prelua datele din momentul in care jocul s-a terminat si le vom folosi pentru a afisa fereastra cu play again unde se afla
            scorul din meciul respectiv, cel mai mare scor din sesiunea de joc dar si doua butoane, unul pentru "Play again", altul pentru "Quit Game".
        :param final_score: reprezinta scorul final din meciul abia terminat
        :param best_scoree: reprezinta best score-ul din sesiunea actuala de joc
        :param w: reprezinta latimea ferestrei de joc
        :param h: reprezinta inaltimea ferestrei de joc
        """
        self.w = w
        self.h = h
        self.score = final_score
        self.best_score = best_scoree
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Snake')

    def play_again(self):
        """
        Aceasta functie este responsabila cu randarea ferestrei de final de joc, unde sunt afisate scorurile si butoanele care ofera posibilitatea
            de a juca din nou sau de a parasi sesiunea de joc curenta.
        :return:
        """
        while self.play is False:
            self.display.fill(background)
            text = font.render("Final Score: " + str(self.score), True, GREEN)
            text2 = font.render("Best Score: " + str(self.best_score), True, GREEN)
            self.display.blit(text, [self.w / 2 - 77, self.h / 4])
            self.display.blit(text2, [self.w / 2 - 75, self.h / 6])
            play_again = Button(self.w / 2 - 90, self.h / 3, "Play Again", self.display)
            if play_again.draw_button():
                self.play = True
            quit_game = Button(self.w / 2 - 90, self.h / 2 + 20, "Quit Game", self.display)
            quit_game.draw_button()
            pygame.display.update()
            event = pygame.event.poll()
            if quit_game.draw_button():
                display_best_score()
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        return self.play


class Button:
    width = 180
    height = 40

    def __init__(self, x, y, text, display):
        """
        In constructor vom primi date care ne vor ajuta sa construim un buton.
        :param x: coordonata x a butonului
        :param y: coordonata y a butonului
        :param text: textul afisat pe buton
        :param display: display-ul pygame peste care va fi afisat butonul
        """
        self.x = x
        self.y = y
        self.text = text
        self.display = display

    def draw_button(self):
        """
        Aceasta functie va folosi resursele primite in constructor pentru a esena un buton care va detecta daca a fost apasat si
            va schimba variabila "action" in acest caz.
        :return: Returneaza variabila action, care indica daca butonul a fost apasat sau nu.
        """
        global clicked
        triggered = False
        pozitie = pygame.mouse.get_pos()

        button_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if button_rect.collidepoint(pozitie):
            if pygame.mouse.get_pressed(3)[0] == 1:
                clicked = True
                pygame.draw.rect(self.display, RED, button_rect)
            elif pygame.mouse.get_pressed(3)[0] == 0 and clicked is True:
                clicked = False
                triggered = True
            else:
                pygame.draw.rect(self.display, (255, 255, 0), button_rect)
        else:
            pygame.draw.rect(self.display, GREEN, button_rect)

        text_img = font.render(self.text, True, BLACK)
        text_len = text_img.get_width()
        self.display.blit(text_img, (self.x + int(self.width / 2) - int(text_len / 2), self.y + 5))
        return triggered


if __name__ == '__main__':
    snake = Snake()

    while True:
        end_game, best_score = snake.start_game()
        if end_game:
            break

    pygame.quit()
