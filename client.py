from math import hypot
from socket import socket, AF_INET, SOCK_STREAM
from pygame import *
from threading import Thread
from random import randint

# ================== NETWORK ==================
sock = socket(AF_INET, SOCK_STREAM)
sock.connect(('5.tcp.eu.ngrok.io', 16932))
my_data = list(map(int, sock.recv(64).decode().strip().split(',')))
my_id = my_data[0]
my_player = my_data[1:]
sock.setblocking(False)

# ================== PYGAME ==================
init()
window = display.set_mode((1000, 1000))
clock = time.Clock()
f = font.Font(None, 50)

# ================== GAME STATE ==================
MENU = 0
PLAY = 1
game_state = MENU

# ================== SKINS ==================
skins = [
    (0, 255, 0),
    (0, 0, 255),
    (255, 0, 0),
    (255, 255, 0),
    (0, 0, 0)
]
selected_skin = 0
player_color = skins[0]

# ================== GAME DATA ==================
all_players = []
running = True
lose = False

# ================== RECEIVE ==================
def receive_data():
    global all_players, lose
    while running:
        try:
            data = sock.recv(4096).decode().strip()
            if data == "LOSE":
                lose = True
            elif data:
                parts = data.strip('|').split('|')
                all_players = [
                    list(map(int, p.split(',')))
                    for p in parts if len(p.split(',')) == 4
                ]
        except:
            pass

Thread(target=receive_data, daemon=True).start()

# ================== FOOD ==================
class Eat:
    def __init__(self, x, y, r, c):
        self.x = x
        self.y = y
        self.radius = r
        self.color = c

    def check_collision(self, px, py, pr):
        return hypot(self.x - px, self.y - py) <= self.radius + pr

eats = [
    Eat(randint(-2000, 2000), randint(-2000, 2000), 10,
        (randint(0,255), randint(0,255), randint(0,255)))
    for _ in range(300)
]

# ================== MENU ==================
def draw_menu():
    window.fill((230, 230, 230))
    title = f.render("Choose your skin", True, (0, 0, 0))
    window.blit(title, (350, 150))

    for i, color in enumerate(skins):
        x = 200 + i * 150
        y = 450
        draw.circle(window, color, (x, y), 40)
        if i == selected_skin:
            draw.circle(window, (0, 0, 0), (x, y), 45, 3)

    info = f.render("A / D - choose | ENTER - start", True, (0, 0, 0))
    window.blit(info, (250, 650))

# ================== MAIN LOOP ==================
while running:
    for e in event.get():
        if e.type == QUIT:
            running = False

        if game_state == MENU and e.type == KEYDOWN:
            if e.key == K_a:
                selected_skin = (selected_skin - 1) % len(skins)
            if e.key == K_d:
                selected_skin = (selected_skin + 1) % len(skins)
            if e.key == K_RETURN:
                player_color = skins[selected_skin]
                game_state = PLAY

    # ---------- MENU ----------
    if game_state == MENU:
        draw_menu()
        display.update()
        clock.tick(60)
        continue

    # ---------- GAME ----------
    window.fill((255, 255, 255))
    scale = max(0.3, min(50 / my_player[2], 1.5))

    # other players
    for p in all_players:
        if p[0] == my_id:
            continue
        sx = int((p[1] - my_player[0]) * scale + 500)
        sy = int((p[2] - my_player[1]) * scale + 500)
        draw.circle(window, (255, 0, 0), (sx, sy), int(p[3] * scale))

    # my player
    draw.circle(window, player_color, (500, 500), int(my_player[2] * scale))

    # food
    to_remove = []
    for eat in eats:
        if eat.check_collision(my_player[0], my_player[1], my_player[2]):
            to_remove.append(eat)
            my_player[2] += int(eat.radius * 0.2)
        else:
            sx = int((eat.x - my_player[0]) * scale + 500)
            sy = int((eat.y - my_player[1]) * scale + 500)
            draw.circle(window, eat.color, (sx, sy), int(eat.radius * scale))

    for eat in to_remove:
        eats.remove(eat)

    if lose:
        t = f.render('U lose!', True, (244, 0, 0))
        window.blit(t, (400, 500))

    display.update()
    clock.tick(60)

    # movement + send
    if not lose:
        keys = key.get_pressed()
        if keys[K_w]: my_player[1] -= 15
        if keys[K_s]: my_player[1] += 15
        if keys[K_a]: my_player[0] -= 15
        if keys[K_d]: my_player[0] += 15

        try:
            msg = f"{my_id},{my_player[0]},{my_player[1]},{my_player[2]}"
            sock.send(msg.encode())
        except:
            pass

quit()
