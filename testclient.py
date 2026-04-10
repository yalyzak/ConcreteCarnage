import random
import time

from Client import Client
from MAP import main_game_object


def random_input(num_keys=32):
    # random key presses (True/False)
    keys = [random.random() < 0.3 for _ in range(num_keys)]  # 30% chance pressed

    # random mouse movement
    dx = random.randint(-50, 50)
    dy = random.randint(-50, 50)

    # realistic frame delta (~60 FPS)
    dt = random.uniform(0.013, 0.02)

    return keys, dx, dy, dt


player = main_game_object()
c = player.Client
c.name = "Player1" # must change name
c.login()  # test login
psw = c.find_room()  # test find room
c.join_room(psw)  # test join room
time.sleep(1)

start = time.perf_counter()
# c.respawn()

while True:  # test ping
    c.send_ping()
    c.receive_tcp()
    # c.send_input(*random_input())
    c.send_chat("test")  # test chat
    time.sleep(0.5)


c.send_chat("test")     # test chat
time.sleep(1)
c.send_chat("fuck")     # test chat profanity
time.sleep(0.1)

c.despawn()
# time.sleep(0.5)
#c.leave_room()
# c.logout()  # test logout
