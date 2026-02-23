# client.py
import socket
import struct
import time

SERVER = "127.0.0.1"
PACK_FORMAT = "BIIhhd"

class Client:

    def __init__(self, name):
        self.name = name
        self.id = None

        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def attach(self, owner_object):
        self.input = owner_object.PlayerController.input_queue.popleft
    def Update(self, dt):
        bools, dx, dy = self.input()
        self.send_input(bools, dx, dy)
        ping = self.ping()
    def Start(self):
        # c = Client("Player1")
        self.login()
        self.create_room("room1")
    def login(self):
        self.tcp.connect((SERVER, 5000))
        self.tcp.send(self.name.encode())

        msg = self.tcp.recv(128).decode()
        self.id = int(msg.split()[1])

    def create_room(self, room):
        self.tcp.send(f"CREATE {room}".encode())
        print(self.tcp.recv(128).decode())

    def join_room(self, room, pwd):
        self.tcp.send(f"JOIN {room} {pwd}".encode())
        print(self.tcp.recv(128).decode())

    def send_input(self, keys, dx, dy):
        mask = 0
        for i, pressed in enumerate(keys):
            if pressed:
                mask |= (1 << i)

        packet = struct.pack(
            PACK_FORMAT,
            1,
            self.id,
            mask,
            dx,
            dy,
            0.0
        )

        self.udp.sendto(packet, (SERVER, 5001))

    def ping(self):
        now = time.perf_counter()

        packet = struct.pack(
            PACK_FORMAT,
            2,
            self.id,
            0,
            0,
            0,
            now
        )

        self.udp.sendto(packet, (SERVER, 5001))

        self.udp.settimeout(1)

        try:
            data, _ = self.udp.recvfrom(1024)
            ptype, _, _, _, _, ts = struct.unpack(PACK_FORMAT, data)

            if ptype == 3:
                ping = (time.perf_counter() - ts) * 1000
                return ping
                print(f"Ping: {ping:.3f} ms")

        except:
            return None
            print("Ping timeout")

# =====================

# c = Client("Player1")
# c.login()
#
# mode = input("create/join: ")
#
# if mode == "create":
#     c.create_room("room1")
# else:
#     pwd = input("password:")
#     c.join_room("room1", pwd)
#
# while True:
#     keys = [False] * 32
#     keys[0] = True    # example key
#     keys[30] = True   # left click
#     keys[31] = False  # right click
#
#     c.send_input(keys, 5, -3)
#     c.ping()

