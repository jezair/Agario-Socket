import pygame as p
from pygame import *
from random import randint
from math import hypot
from socket import *
from threading import Thread

# Подключение к серверу
try:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(('localhost', 8080))
    my_data = list(map(int, sock.recv(64).decode().strip().split(',')))
    my_id = my_data[0]
    my_player = my_data[1:]
    my_player.append(0)  # Добавляем опыт (exp)
except:
    my_id = 0
    my_player = [0, 0, 20, 0]  # x, y, radius, exp

all_players = []
running = True
lose = False


def receive_data():
    global all_players, running, lose
    while running:
        try:
            data = sock.recv(4096).decode().strip()
            if data == "LOSE":
                lose = True
            elif data:
                packets = data.strip("|").split("|")
                all_players = []
                for packet in packets:
                    if packet and ',' in packet:
                        parts = packet.split(",")
                        if len(parts) == 5:
                            all_players.append(list(map(int, parts)))
        except:
            pass


Thread(target=receive_data, daemon=True).start()

init()

player_speed = 15
win_size = (1200, 1000)
DARK_GRAY = (40, 40, 40)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (50, 150, 255)
RED = (255, 50, 50)
GRID_COLOR = (50, 50, 50)

window = display.set_mode(win_size)
clock = time.Clock()

# Шрифты
font_large = p.font.Font(None, 36)
font_medium = p.font.Font(None, 28)
font_small = p.font.Font(None, 24)


class Eat:
    def __init__(self, x, y, r, c):
        self.x = x
        self.y = y
        self.radius = r
        self.color = c

    def check_collision(self, player_x, player_y, player_r):
        nx = self.x - player_x
        ny = self.y - player_y
        return hypot(nx, ny) <= self.radius + player_r


# Начальная генерация еды
def generate_food(count):
    return [Eat(randint(-2000, 2000), randint(-2000, 2000), 10,
                (randint(0, 255), randint(0, 255), randint(0, 255)))
            for i in range(count)]


eats = generate_food(500)
last_regen_time = time.get_ticks()

while running:
    for e in event.get():
        if e.type == QUIT:
            running = False
            quit()

    window.fill(DARK_GRAY)

    # Рисуем сетку на фоне
    scale = max(0.01, min(1.0, 30.0 / (my_player[2] ** 0.7)))

    grid_size = 50
    offset_x = int(my_player[0] * scale) % grid_size
    offset_y = int(my_player[1] * scale) % grid_size

    for x in range(-offset_x, win_size[0], grid_size):
        draw.line(window, GRID_COLOR, (x, 0), (x, win_size[1]), 1)
    for y in range(-offset_y, win_size[1], grid_size):
        draw.line(window, GRID_COLOR, (0, y), (win_size[0], y), 1)

    # Управление игроком
    if lose == False:
        keys = key.get_pressed()
        # Скорость уменьшается с размером
        speed = max(3, 18 - my_player[2] // 15)
        if keys[K_w]:
            my_player[1] -= speed
        if keys[K_s]:
            my_player[1] += speed
        if keys[K_a]:
            my_player[0] -= speed
        if keys[K_d]:
            my_player[0] += speed

    # Динамическое масштабирование - используем степенную функцию для плавного отдаления
    # При размере 20 → scale ≈ 1.0
    # При размере 100 → scale ≈ 0.3
    # При размере 500 → scale ≈ 0.08
    # При размере 2000+ → scale → 0.01 (минимум)
    scale = max(0.01, min(1.0, 30.0 / (my_player[2] ** 0.7)))

    # Отрисовка других игроков
    for pl in all_players:
        if pl[0] != my_id:
            ex = int((pl[1] - my_player[0]) * scale + 500)
            ey = int((pl[2] - my_player[1]) * scale + 500)
            radius = int(pl[3] * scale)
            if -100 <= ex <= win_size[0] + 100 and -100 <= ey <= win_size[1] + 100:
                draw.circle(window, RED, (ex, ey), max(2, radius))
                # Отображение ID
                if radius > 10:
                    id_text = font_small.render(f"#{pl[0]}", True, WHITE)
                    window.blit(id_text, (ex - 15, ey - radius - 20))

    # Отрисовка своего игрока (всегда в центре)
    player_radius = max(2, int(my_player[2] * scale))
    draw.circle(window, BLUE, (500, 500), player_radius)
    if player_radius > 10:
        id_text = font_small.render(f"#{my_id}", True, WHITE)
        window.blit(id_text, (485, 500 - player_radius - 20))

    # Проверка поедания еды и отрисовка
    to_remove = []
    for eat in eats:
        if eat.check_collision(my_player[0], my_player[1], my_player[2]):
            to_remove.append(eat)
            my_player[2] += int(eat.radius * 0.2)
            my_player[3] += 10  # Добавляем опыт
        else:
            ex = int((eat.x - my_player[0]) * scale + 500)
            ey = int((eat.y - my_player[1]) * scale + 500)
            radius = int(eat.radius * scale)
            if -50 <= ex <= win_size[0] + 50 and -50 <= ey <= win_size[1] + 50 and radius > 1:
                draw.circle(window, eat.color, (ex, ey), max(2, radius))

    for eat in to_remove:
        eats.remove(eat)

    # Регенерация еды каждые 2 секунды
    current_time = time.get_ticks()
    if current_time - last_regen_time > 2000:
        needed = 500 - len(eats)
        if needed > 0:
            new_food = generate_food(needed)
            eats.extend(new_food)
        last_regen_time = current_time

    # Отрисовка таблицы лидеров
    leaderboard_x = 1000
    leaderboard_y = 20
    leaderboard_width = 180

    # Заголовок таблицы лидеров
    title = font_large.render("Лидеры", True, WHITE)
    window.blit(title, (leaderboard_x + 30, leaderboard_y))

    # Подготовка данных для таблицы
    leaderboard_data = []
    for pl in all_players:
        leaderboard_data.append((pl[0], pl[4]))  # id, exp

    # Добавляем себя
    leaderboard_data.append((my_id, my_player[3]))

    # Сортировка по опыту
    leaderboard_data.sort(key=lambda x: x[1], reverse=True)

    # Отрисовка топ-10
    y_offset = leaderboard_y + 50
    for i, (pid, exp) in enumerate(leaderboard_data[:10]):
        if pid == my_id:
            color = BLUE
        else:
            color = WHITE

        rank_text = font_medium.render(f"{i + 1}.", True, color)
        player_text = font_medium.render(f"Игрок #{pid}", True, color)
        exp_text = font_medium.render(f"{exp} XP", True, color)

        window.blit(rank_text, (leaderboard_x, y_offset))
        window.blit(player_text, (leaderboard_x + 30, y_offset))
        window.blit(exp_text, (leaderboard_x + 130, y_offset))
        y_offset += 30

    # Отображение своих характеристик
    zoom_percent = int(scale * 100)
    info_text = font_medium.render(f"Размер: {my_player[2]} | Опыт: {my_player[3]} | Зум: {zoom_percent}%", True, WHITE)
    window.blit(info_text, (10, 10))

    # Количество еды на карте
    food_text = font_small.render(f"Еда: {len(eats)}", True, WHITE)
    window.blit(food_text, (10, 45))

    # Сообщение о поражении
    if lose:
        lose_text = font_large.render("ВЫ ПРОИГРАЛИ!", True, RED)
        window.blit(lose_text, (win_size[0] // 2 - 120, win_size[1] // 2))

    display.update()
    clock.tick(60)

    # Отправка данных на сервер
    if not lose:
        try:
            msg = f"{my_id},{my_player[0]},{my_player[1]},{my_player[2]},{my_player[3]}"
            sock.send(msg.encode())
        except:
            pass

sock.close()