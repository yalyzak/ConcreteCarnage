# server.py
import socket
import threading
import struct
import random
import string
import select

HOST = "0.0.0.0"
TCP_PORT = 5000
UDP_PORT = 5001

PACK_FORMAT = "BIIhhd"

# =====================
# OBJECTS
# =====================

class Client:
    def __init__(self, cid, username):
        self.id = cid
        self.username = username
        self.room = None
        self.udp_addr = None

class Room:
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.clients = []

    def add_client(self, client):
        if client not in self.clients:
            self.clients.append(client)
            client.room = self

    def broadcast(self, data, sender, udp):
        for c in self.clients:
            if c != sender and c.udp_addr:
                udp.sendto(data, c.udp_addr)

class RoomManager:
    def __init__(self):
        self.rooms = {}

    def generate_password(self):
        return ''.join(random.choice(string.ascii_letters+string.digits) for _ in range(6))

    def create_room(self, name, owner):
        if name in self.rooms:
            return None

        pwd = self.generate_password()
        room = Room(name, pwd)
        room.add_client(owner)  # auto join
        self.rooms[name] = room
        return pwd

    def join_room(self, name, pwd, client):
        room = self.rooms.get(name)
        if not room:
            return False
        if room.password != pwd:
            return False

        room.add_client(client)
        return True

# =====================

clients = {}
room_manager = RoomManager()
next_id = 1

# =====================
# TCP
# =====================

def tcp_thread(conn):
    global next_id

    username = conn.recv(128).decode()
    cid = next_id
    next_id += 1

    client = Client(cid, username)
    clients[cid] = client

    conn.send(f"LOGIN {cid}".encode())

    while True:
        try:
            data = conn.recv(256).decode()
            if not data:
                break

            cmd = data.split()

            if cmd[0] == "CREATE":
                room = cmd[1]
                pwd = room_manager.create_room(room, client)

                if pwd:
                    conn.send(f"created a room with this password {pwd}".encode())
                else:
                    conn.send(b"EXISTS")

            elif cmd[0] == "JOIN":
                ok = room_manager.join_room(cmd[1], cmd[2], client)
                conn.send(b"JOINED" if ok else b"FAILED")

        except:
            break

    conn.close()

def tcp_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, TCP_PORT))
    s.listen()

    while True:
        conn, _ = s.accept()
        threading.Thread(target=tcp_thread, args=(conn,)).start()

# =====================
# UDP
# =====================

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind(("0.0.0.0", 5001))

# VERY IMPORTANT
udp.setblocking(False)

MAX_PACKETS_PER_TICK = 256


def udp_server():

    while True:

        # ---------------------------------
        # NON-BLOCKING WAIT
        # ---------------------------------
        readable, _, _ = select.select(
            [udp],  # sockets to watch
            [],
            [],
            0.002   # max wait time (2ms tick)
        )

        if not readable:
            continue  # nothing arrived

        # ---------------------------------
        # PROCESS MANY PACKETS
        # ---------------------------------
        while True:
            try:
                data, addr = udp.recvfrom(1024)
            except BlockingIOError:
                break

            ptype, cid, keys, dx, dy, timestamp = struct.unpack(
                PACK_FORMAT, data
            )
            keys = [(keys >> i) & 1 == 1 for i in range(4)]

            if cid not in clients:
                continue

            client = clients[cid]
            client.udp_addr = addr

            if ptype == 2:  # ping
                pong = struct.pack(
                    PACK_FORMAT,
                    3, cid, 0, 0, 0, timestamp
                )
                udp.sendto(pong, addr)
                continue

            if client.room:
                client.room.broadcast(data, client, udp)

threading.Thread(target=tcp_server).start()
threading.Thread(target=udp_server).start()

print("Server running")