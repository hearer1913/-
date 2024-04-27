import json
import random
import socket
import sys
import asyncio

import pygame

pygame.init()

# Установка размеров окна
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Меню Pygame")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)

# Шрифт
font = pygame.font.Font(None, 36)
# Параметры окна
WINDOW_SIZE = (WIDTH, HEIGHT)
WINDOW_TITLE = 'Игра в покер на костях'
BG_COLOR = (255, 255, 255)

# Параметры костей
DICE_SIZE = HEIGHT // 6
DICE_COLOR = BLACK
DOT_COLOR = RED
DOT_RADIUS = 10
DOT_MARGIN = 20
DICE_MARGIN = 50
GAP = 0

# Переменная для отслеживания текущего меню
current_menu = None

# Игровые переменные
RUNNING = True
PLAYING = False
CONNECTED = False
ROLLING = False
SECOND_PLAYER = False
RDICE = "00000"  # Данные о костях


class GameData:
    dice_values = "0" * 5  # Изначально все кости показывают 0
    selected_dice = [True for _ in range(5)]
    rolling = False
    rund: float = 1  # Счетчик раундов заготовка
    now_round: int = 1
    canReroll = False
    canNextRound = False
    imReady = False
    wins = 0
    draws = 0

    @classmethod
    def reverse_dice(cls, index):
        cls.selected_dice[index] = not cls.selected_dice[index]

    @classmethod
    def reset_dice(cls):
        cls.dice_values = "0" * 5
        cls.selected_dice = [True for _ in range(5)]

    @classmethod
    def clear_data(cls):
        cls.dice_values = "0" * 5  # Изначально все кости показывают 1
        cls.selected_dice = [True for _ in range(5)]
        cls.rolling = False
        cls.canReroll = False
        cls.rund = 1
        cls.now_round = 1
        cls.canNextRound = False
        cls.imReady = False
        cls.wins = 0
        cls.draws = 0


# Функция для сохранения настроек в файл JSON
def save_settings(settings):
    with open("settings.json", "w") as file:
        json.dump(settings, file)


# Функция для загрузки настроек из файла JSON и их применения
def load_settings():
    try:
        with open("settings.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"bone_color": BLACK}  # Устанавливаем черный цвет по умолчанию


# Функция для установки цвета костей
def set_bone_color(color):
    settings["bone_color"] = color
    load_bone_color()
    save_settings(settings)


def load_bone_color():
    global DICE_COLOR, DOT_COLOR
    DICE_COLOR = BLACK if tuple(settings["bone_color"]) == BLACK else GRAY
    DOT_COLOR = RED if tuple(DICE_COLOR) == BLACK else BLACK


# Функции для действий при нажатии на кнопки
def main_menu():
    global current_menu
    current_menu = None


def start_game():
    global PLAYING
    PLAYING = True  # Запускаем игру при выборе "Играть"


def choose_bone_color():
    global current_menu
    current_menu = "bone_color"


def exit_game():
    pygame.quit()
    sys.exit()


# Функция для отображения текста на экране
def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    text_rect.center = (x, y)
    surface.blit(text_obj, text_rect)


# Функция для создания кнопок
def draw_button(text, x, y, width, height, color, hover_color, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if x < mouse[0] < x + width and y < mouse[1] < y + height:
        pygame.draw.rect(screen, hover_color, (x, y, width, height))
        if click[0] == 1 and action is not None:
            action()
    else:
        pygame.draw.rect(screen, color, (x, y, width, height))

    draw_text(text, font, BLACK, screen, x + width / 2, y + height / 2)


# Функция для вывода названия комбинации на экран
def display_combination(combination):
    font = pygame.font.Font(None, HEIGHT // 16)
    text = font.render("Комбинация: " + combination, True, (0, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 12))
    screen.blit(text, text_rect)


# # Функция для вывода названия комбинации на экран
def display_wins_our():
    font = pygame.font.Font(None, HEIGHT // 20)
    text = font.render("Побед: " + str(GameData.wins), True, (0, 0, 0))
    text_rect = text.get_rect(center=(WIDTH - 100, 20))
    screen.blit(text, text_rect)


# # Функция для вывода названия комбинации на экран
def display_wins_ksenos():
    font = pygame.font.Font(None, HEIGHT // 20)
    text = font.render("Побед: " + str(GameData.now_round - GameData.wins - GameData.draws - 1), True, (0, 0, 0))
    text_rect = text.get_rect(center=(WIDTH - 100, HEIGHT - 20))
    screen.blit(text, text_rect)


# Функция для вывода названия чужой комбинации на экран
def rdisplay_combination(rcombination):
    font = pygame.font.Font(None, HEIGHT // 16)
    text = font.render("Комбинация: " + rcombination, True, (0, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT * 11 // 12))
    screen.blit(text, text_rect)


# Функция для вывода номера раунда
def display_round(rou):
    font = pygame.font.Font(None, HEIGHT // 16)
    text = font.render("Раунд: " + str(rou), True, (0, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 4, HEIGHT // 12))
    screen.blit(text, text_rect)


def display_win():
    font = pygame.font.Font(None, HEIGHT // 16)
    text = font.render("ПОБЕДА!", True, (32, 218, 32))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)


def display_draw():
    font = pygame.font.Font(None, HEIGHT // 16)
    text = font.render("НИЧЬЯ", True, (111, 111, 111))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)


def display_lose():
    font = pygame.font.Font(None, HEIGHT // 16)
    text = font.render("ПОРАЖЕНИЕ!", True, (218, 32, 32))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)


# Функция для воспроизведения звукового эффекта
def play_sound_effect():
    pygame.mixer.Sound("dice_roll.wav").play()


# Функция для отрисовки своих костей
def draw_dice():
    global WIDTH, HEIGHT, DICE_SIZE, DOT_RADIUS, DOT_MARGIN, DICE_MARGIN, GAP  # ...
    # Подстройка параметров под размер экрана, если он изменился
    if (WIDTH, HEIGHT) != pygame.display.get_surface().get_size():
        WIDTH, HEIGHT = pygame.display.get_surface().get_size()

        DICE_SIZE = HEIGHT // 6
        DOT_RADIUS = HEIGHT // 60
        DOT_MARGIN = HEIGHT // 30
        DICE_MARGIN = HEIGHT // 20

        GAP = WIDTH // 2 - (DICE_SIZE * 5 + DICE_MARGIN * 6) // 2

    pygame.draw.line(screen, BLACK, [0, 0], [WIDTH, 0], 3)
    pygame.draw.line(screen, BLACK, [0, HEIGHT // 2], [WIDTH, HEIGHT // 2], 3)

    dice_x = DICE_MARGIN + GAP
    for i, value in enumerate(GameData.dice_values):
        pygame.draw.rect(screen, DICE_COLOR, (dice_x, HEIGHT // 4 - DICE_SIZE // 2, DICE_SIZE, DICE_SIZE))
        if GameData.selected_dice[i]:
            # Отображение выбранных костей зеленой рамкой
            pygame.draw.rect(screen, (0, 255, 0),
                             (dice_x - 2, HEIGHT // 4 - DICE_SIZE // 2 - 2, DICE_SIZE + 4, DICE_SIZE + 4), 3)
        if value == "1":
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE // 2, HEIGHT // 4), DOT_RADIUS)
        elif value == "2":
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 4 - DOT_MARGIN), DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 4 + DOT_MARGIN),
                               DOT_RADIUS)
        elif value == "3":
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 4 - DOT_MARGIN), DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE // 2, HEIGHT // 4), DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 4 + DOT_MARGIN),
                               DOT_RADIUS)
        elif value == "4":
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 4 - DOT_MARGIN), DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 4 - DOT_MARGIN),
                               DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 4 + DOT_MARGIN), DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 4 + DOT_MARGIN),
                               DOT_RADIUS)
        elif value == "5":
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 4 - DOT_MARGIN), DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 4 - DOT_MARGIN),
                               DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 4 + DOT_MARGIN), DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 4 + DOT_MARGIN),
                               DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE // 2, HEIGHT // 4), DOT_RADIUS)
        elif value == "6":
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 4 - DOT_MARGIN), DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 4 - DOT_MARGIN),
                               DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 4), DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 4), DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 4 + DOT_MARGIN), DOT_RADIUS)
            pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 4 + DOT_MARGIN),
                               DOT_RADIUS)
        dice_x += DICE_SIZE + DICE_MARGIN


def roll_dice():
    dice_values = "".join([str(random.randint(1, 6)) if GameData.selected_dice[i] else value for i, value in enumerate(GameData.dice_values)])
    GameData.dice_values = dice_values
    return dice_values


# 01011
# rdice_values -> 352


# Функция для отрисовки чужих костей
def rdraw_dice(rdice_values):
    global WIDTH, HEIGHT, DICE_SIZE, DOT_RADIUS, DOT_MARGIN, DICE_MARGIN, GAP, RDICE
    RDICE = rdice_values
    dice_x = DICE_MARGIN + GAP
    for value in RDICE:
        pygame.draw.rect(screen, DICE_COLOR, (dice_x, HEIGHT // 1.3 - DICE_SIZE // 2, DICE_SIZE, DICE_SIZE))
        match value:
            case "1":
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE // 2, HEIGHT // 1.3), DOT_RADIUS)
            case "2":
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 1.3 - DOT_MARGIN), DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 1.3 + DOT_MARGIN),
                                   DOT_RADIUS)
            case "3":
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 1.3 - DOT_MARGIN), DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE // 2, HEIGHT // 1.3), DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 1.3 + DOT_MARGIN),
                                   DOT_RADIUS)
            case "4":
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 1.3 - DOT_MARGIN), DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 1.3 - DOT_MARGIN),
                                   DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 1.3 + DOT_MARGIN), DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 1.3 + DOT_MARGIN),
                                   DOT_RADIUS)
            case "5":
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 1.3 - DOT_MARGIN), DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 1.3 - DOT_MARGIN),
                                   DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 1.3 + DOT_MARGIN), DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 1.3 + DOT_MARGIN),
                                   DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE // 2, HEIGHT // 1.3), DOT_RADIUS)
            case "6":
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 1.3 - DOT_MARGIN), DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 1.3 - DOT_MARGIN),
                                   DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 1.3), DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 1.3), DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DOT_MARGIN, HEIGHT // 1.3 + DOT_MARGIN), DOT_RADIUS)
                pygame.draw.circle(screen, DOT_COLOR, (dice_x + DICE_SIZE - DOT_MARGIN, HEIGHT // 1.3 + DOT_MARGIN),
                                   DOT_RADIUS)
        dice_x += DICE_SIZE + DICE_MARGIN


def rroll_dice(selected_dice: str):
    rdice_values = "".join([str(random.randint(1, 6)) for _ in range(selected_dice.count("1"))])
    return rdice_values


def send_request(request: str):
    conn = ("169.254.41.127", 5005)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(request.encode(), conn)
        sock.settimeout(5)
        try:
            data = sock.recv(1024)
        except TimeoutError:
            return "500"
        return data.decode()


# Функция для проверки комбинации костей
def check_combination(dice_values):
    # Сортируем кости
    if 0 in dice_values:
        return None
    sorted_dice = sorted(dice_values)
    # Проверяем наличие покера (все кости одного достоинства)
    if len(set(sorted_dice)) == 1:
        return "Покер"
    # Проверяем наличие каре (четыре кости одного достоинства)
    if len(set(sorted_dice)) == 2:
        for value in set(sorted_dice):
            if sorted_dice.count(value) == 4:
                return "Каре"
    # Проверяем наличие фул-хауса (пары и сет костей разных достоинств)
    if len(set(sorted_dice)) == 2:
        for value in set(sorted_dice):
            if sorted_dice.count(value) == 3:
                return "Фул-хаус"
    # Проверяем наличие большого стрейта (все кости разного достоинства в последовательности от 2 до 6)
    if sorted_dice == [2, 3, 4, 5, 6]:
        return "Большой стрейт"
    # Проверяем наличие малого стрейта (все кости разного достоинства в последовательности от 1 до 5)
    if sorted_dice == [1, 2, 3, 4, 5]:
        return "Малый стрейт"
    # Проверяем наличие сета (три кости одного достоинства)
    if len(set(sorted_dice)) == 3:
        for value in set(sorted_dice):
            if sorted_dice.count(value) == 3:
                return "Сет"
    # Проверяем наличие двух пар (две пары костей одного достоинства каждая)
    if len(set(sorted_dice)) == 3:
        return "Две пары"
    # Проверяем наличие пары (две кости одного достоинства)
    if len(set(sorted_dice)) == 4:
        return "Пара"
    # Если ничего не подходит, то возвращаем "Ничего"
    return "Ничего"


def check_ball(combination):
    if combination == "Покер":
        return 9
    if combination == "Каре":
        return 8
    if combination == "Фул-хаус":
        return 7
    if combination == "Большой стрейт":
        return 6
    if combination == "Малый стрейт":
        return 5
    if combination == "Сет":
        return 4
    if combination == "Две пары":
        return 3
    if combination == "Пара":
        return 2
    if combination == "Ничего":
        return 1


async def run_command(com, *args):
    await asyncio.sleep(.2)
    com(args if len(args) > 1 else args[0] if args else None)


# Основная функция игры + сеть
def game():
    global CONNECTED, PLAYING, ROLLING, SECOND_PLAYER, RDICE
    if CONNECTED:
        response: str = send_request("STEAL")
    else:
        response: str = send_request("START")

    match response:
        case "500":  # Проблема сервера, разрываем всё
            CONNECTED = False
            PLAYING = False
            ROLLING = False
            SECOND_PLAYER = False
            GameData.clear_data()
        case "400":  # Проблема клиента, разрываем всё
            CONNECTED = False
            PLAYING = False
            ROLLING = False
            SECOND_PLAYER = False
            GameData.clear_data()
        case "200":  # Всё зашибись, все как надо
            CONNECTED = True
        case data:  # Проверка иной информации в ответе
            if int(GameData.now_round) == 4:
                wins = GameData.wins
                loses = 3 - GameData.wins - GameData.draws
                if wins == loses:
                    display_draw()
                elif wins < loses:
                    display_lose()
                else:
                    display_win()
                return

            draw_dice()
            display_round(int(GameData.now_round))
            if data == "0":  # Ожидание второго игрока
                return
            elif not SECOND_PLAYER:
                SECOND_PLAYER = True
            elif "/" in data:  # Противник роллит
                new_dice = rroll_dice(data[1:])  # Засовываются элементы после "/"
                res = ""  # Пустая строчка
                for i, v in enumerate(data[1:]):
                    if v == "1":
                        res += new_dice[0]
                        new_dice = new_dice[1:]
                    else:
                        res += RDICE[i]
                RDICE = res
                # Анимация броска чужих выбранных костей
                rdraw_dice(RDICE)
            else:
                # Отображение данных о чужих костях, данные устоявшиеся
                if data[-1] == "R":
                    data = data[:-1]
                    GameData.canNextRound = True
                rdraw_dice(data)
                ksenos_dice = [int(i) for i in data]
                rcombination = check_combination(ksenos_dice)
                if rcombination is not None:
                    rdisplay_combination(rcombination)

            if ROLLING:
                if GameData.canReroll: GameData.canReroll = False
                # Посылаются данные о своих выбранных костях, эти данные идут после "/"
                send_request("SEND/1/" + "".join(map(lambda d: str(int(d)), GameData.selected_dice)))
                # Анимация броска своих костей
                play_sound_effect()  # Воспроизведение звукового эффекта при начале анимации
                roll_dice()
            else:  # Если анимация переброса костей завершилась, отображаем комбинацию
                all_dice = [int(i) for i in GameData.dice_values]
                combination = check_combination(all_dice)
                display_wins_our()
                display_wins_ksenos()

                if GameData.canNextRound and GameData.now_round == GameData.rund:
                    GameData.canNextRound = False

                if combination is not None:
                    display_combination(combination)
                if GameData.imReady and GameData.canNextRound:
                    my = check_ball(combination)
                    thier = check_ball(check_combination([int(i) for i in data]))

                    if my > thier:
                        GameData.wins += 1
                    elif my == thier:
                        GameData.draws += 1

                    if GameData.rund % 1:
                        GameData.rund += 0.5
                    GameData.now_round += 1
                    GameData.imReady = False
                    GameData.canNextRound = False
                    asyncio.run(run_command(send_request, "SEND/2"))

                elif "0" not in GameData.dice_values and GameData.now_round == GameData.rund and not GameData.canReroll:
                    GameData.canReroll = True
                    GameData.rund += 0.5
                elif GameData.rund % 1 and not GameData.canReroll:
                    GameData.rund += 0.5
                if GameData.rund == GameData.now_round and "0" not in GameData.dice_values:
                    GameData.reset_dice()
                    send_request("SEND/" + GameData.dice_values)


# Загрузка настроек
settings = load_settings()
load_bone_color()

clock = pygame.time.Clock()
while RUNNING:
    clock.tick(15)
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            RUNNING = False
            if CONNECTED:
                send_request("LEAVE")
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and CONNECTED:
                CONNECTED = False
                PLAYING = False
                ROLLING = False
                SECOND_PLAYER = False
                GameData.clear_data()
                send_request("LEAVE")
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5) and not ROLLING and PLAYING and SECOND_PLAYER and GameData.canReroll:
                GameData.reverse_dice(event.key - pygame.K_1)
            elif event.key == pygame.K_SPACE and PLAYING and SECOND_PLAYER and (ROLLING or (True in GameData.selected_dice and GameData.rund - GameData.now_round < 1)):
                if ROLLING:
                    # Посылаются данные о своих костях
                    send_request("SEND/" + GameData.dice_values)
                ROLLING = not ROLLING
            elif event.key == pygame.K_RETURN and not GameData.imReady and (GameData.rund % 1 or GameData.now_round < GameData.rund):
                GameData.canReroll = False
                GameData.imReady = True
                send_request("SEND/2")
            elif PLAYING and event.key == pygame.K_d and pygame.key.get_mods() & pygame.KMOD_SHIFT and pygame.key.get_mods() & pygame.KMOD_CTRL:
                send_request("DEV")  # Добавление бота для отладки

    screen.fill(WHITE)

    if PLAYING:
        game()
        pygame.display.update()
        continue

    # Отображение кнопок в зависимости от текущего меню
    if current_menu is None:
        draw_button("Играть", 350, 200, 100, 50, GRAY, BLACK, start_game)
        draw_button("Выбор цвета костей", 250, 300, 300, 50, GRAY, BLACK, choose_bone_color)
    elif current_menu == "bone_color":
        draw_button("Черные", 250, 200, 300, 50, GRAY, BLACK, lambda: set_bone_color(BLACK))
        draw_button("Серые", 250, 300, 300, 50, GRAY, BLACK, lambda: set_bone_color(GRAY))
        draw_button("Назад", 350, 400, 100, 50, GRAY, BLACK, main_menu)

    draw_button("Выход", 350, 500, 100, 50, GRAY, BLACK, exit_game)

    # Обновление экрана
    pygame.display.update()

pygame.quit()
