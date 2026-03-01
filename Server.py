import socket
import threading
import struct
import random
import string
import select
from bereshit import Object, BoxCollider, Rigidbody, Vector3, Camera, Core
from Movement import PlayerController, ServerController
from MAP import crateMAP
from debug import debug
import time

HOST = "0.0.0.0"
TCP_PORT = 5000
UDP_PORT = 5001

CLIENT_PACK_FORMAT = "!BIIhhd"
PING_FORMAT = "!Bd"
STATE_FORMAT = "!B10f"

# =====================
# OBJECTS
# =====================
def game_object(name):
    return Object(name=name, position=Vector3(5,1,0)).add_component(
    [BoxCollider(),
    Rigidbody(Freeze_Rotation=Vector3(1,1,1), useGravity=True, velocity=Vector3(0,0,0)), ServerController(),
    ])
class Client:
    def __init__(self, cid, username):
        self.id = cid
        self.username = username
        self.room = None
        self.udp_addr = None
        self.game_object = game_object(username)
        self.last_ping_time = 0

class Room:
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.clients = []
        camera = Object(name="camera", position=Vector3(0,10,0), rotation=Vector3(90,0,0)).add_component(Camera())
        self.Camera = camera

    def add_client(self, client):
        if client not in self.clients:
            self.clients.append(client)
            self.Camera.add_child(client.game_object)
            client.room = self

    def broadcast(self, data, sender, udp):
        for c in self.clients:
            if c.udp_addr:
            # if c != sender and c.udp_addr:
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
        box = Object(name="box", size=Vector3(10, 1, 5), rotation=Vector3(0, 0, 0)).add_component(
            [BoxCollider(), Rigidbody(isKinematic=True)])

        threading.Thread(target=Core.run, args=([room.Camera, box] + crateMAP(),), kwargs={"Render": True}, daemon=True).start()

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

MAX_PACKETS_PER_TICK = 200
def udp_server():

    while True:

        # ---------------------------------
        # NON-BLOCKING WAIT
        # ---------------------------------
        readable, _, _ = select.select(
            [udp],  # sockets to watch
            [],
            [],
            0.1   # max wait time (2ms tick)
        )

        if not readable:
            continue  # nothing arrived

        # ---------------------------------
        # PROCESS MANY PACKETS
        # ---------------------------------
        data, addr = udp.recvfrom(1024)
        ptype = struct.unpack("!B", data[:1])[0]

        if ptype == 2:  # ping

            _, timestamp = struct.unpack(PING_FORMAT, data)

            pong = struct.pack(
                PING_FORMAT,
                3,
                timestamp
            )

            udp.sendto(pong, addr)

        elif ptype == 1:

            ptype, cid, keys, dx, dy, timestamp = struct.unpack(
                CLIENT_PACK_FORMAT, data
            )
            client = clients[cid]
            client.udp_addr = addr
            if cid not in clients:
                continue
            if not client.room:
                continue
            client.game_object.ServerController.input_controller(keys, 1 / 60)
            client.game_object.ServerController.mouse_controller(dx, dy)
            if time.perf_counter() - client.last_ping_time > 1:
                position = client.game_object.position
                rotation = client.game_object.quaternion
                velocity = client.game_object.Rigidbody.velocity

                data = struct.pack(STATE_FORMAT, 4, position.x, position.y, position.z, rotation.w, rotation.x, rotation.y, rotation.z, velocity.x, velocity.y, velocity.z)
                client.room.broadcast(data, addr, udp)
                client.last_ping_time = time.perf_counter()


threading.Thread(target=tcp_server, daemon=False).start()
threading.Thread(target=udp_server, daemon=False).start()

print("Server running")