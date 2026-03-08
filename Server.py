import socket
import threading
import struct
import random
import string
import select
from collections import deque

from bereshit import Object, BoxCollider, Rigidbody, Vector3, Camera, Core
from Movement import PlayerController, ServerController
from MAP import crateMAP
from debug import debug, debug2
from Shoot import Shoot
from Player import ServerPlayer

import time

from protocol import PacketType, CLIENT_PACK_FORMAT, PING_FORMAT, PONG_FORMAT, STATE_FORMAT, TICK, DEATH_FORMAT


HOST = "0.0.0.0"
TCP_PORT = 5000
UDP_PORT = 5001

# thread-safe collections
clients_lock = threading.Lock()
clients = {}

room_manager_lock = threading.Lock()

# =====================
# OBJECTS
# =====================
def dead_message(cid):
    return struct.pack(DEATH_FORMAT, PacketType.DEATH, cid)

class ClientHelper:
    logout_deque = deque(maxlen=200)

    def __init__(self, client):
        self._client = client
        self.messages_queue = deque(maxlen=20)

    def last_seen(self):
        return self._client.last_seen

    def send(self, message):
        self.messages_queue.append(message)

    def dead(self):
        ClientHelper.logout_deque.append(self._client)

    def Update(self, dt):
        return # needs fixing
        # remove the player if they haven't been heard from in a while
        if time.perf_counter() - self.last_seen() > 3:
            # use the client method in case extra cleanup is added later
            self._client.log_out()
            print("logging out ", self.parent.name)
            self.parent.destroy()


def game_object(name, client):
    return Object(name=name, position=Vector3(5, 1, random.randint(0, 20))).add_component(
        [
            BoxCollider(),
            Rigidbody(Freeze_Rotation=Vector3(1, 1, 1), useGravity=True, velocity=Vector3(0, 0, 0)),
            ServerController(),
            ClientHelper(client),
            Shoot(),
            ServerPlayer()
        ])
class Client:
    def __init__(self, cid, username):
        self.id = cid
        self.username = username
        self.room = None
        self.udp_addr = None
        self.game_object = game_object(username, self)
        self.last_seen = time.perf_counter()
        self.ServerController = self.game_object.ServerController

    def log_out(self):
        self.room.remove_client(self)
class Room:
    def __init__(self, name, password, room_manager):
        self.name = name
        self.password = password
        self.clients = []
        self.room_manager = room_manager
        camera = Object(name="camera", position=Vector3(0,10,0), rotation=Vector3(90,0,0)).add_component(Camera())
        self.Camera = camera
        self.last_broadcast = time.perf_counter()

    def add_client(self, client):
        if client not in self.clients:
            self.clients.append(client)
            self.Camera.add_child(client.game_object)
            client.room = self

    def remove_client(self, client):
        if client in self.clients:
            self.clients.remove(client)
            client.game_object.destroy()

            # Clear the client's room reference
            client.room = None
        if not self.clients:
            # no more players: shut down the physics world
            try:
                if hasattr(self.Camera, 'World'):
                    self.Camera.World.Exit()
            except Exception:
                pass
            # remove from manager
            self.room_manager.remove_room(self.name)
    def broadcast(self, data, udp):
        """Send *data* to every client in the room.

        If *sender* is provided the packet is not echoed back to that
        address; pass None to broadcast to everyone (including the origin).
        """
        for c in self.clients:
            # if not c.udp_addr:
            #     continue
            # if sender is not None and c.udp_addr == sender:
            #     # skip the original sender
            #     continue
            if c.udp_addr:
                udp.sendto(data, c.udp_addr)

class RoomManager:
    def __init__(self):
        self.rooms = {}

    def generate_password(self):
        return ''.join(random.choice(string.ascii_letters+string.digits) for _ in range(6))

    def create_room(self, name, owner):
        with room_manager_lock:
            if name in self.rooms:
                return None

            pwd = self.generate_password()
            pwd = "0" # temp for testing
            room = Room(name, pwd, room_manager)
            room.add_client(owner)  # auto join
            self.rooms[name] = room

            threading.Thread(target=Core.run, args=([room.Camera] + crateMAP(),), kwargs={"Render": True, "tick" : TICK}, daemon=True).start()

            return pwd

    def join_room(self, name, pwd, client):
        with room_manager_lock:
            room = self.rooms.get(name)
            if not room:
                return False
            if room.password != pwd:
                return False

            room.add_client(client)
            return True

    def remove_room(self, room_name):
        with room_manager_lock:
            room = self.rooms.get(room_name)
            if not room:
                return

            print(f"Removing room: {room_name}")

            # Optional: stop game loop / cleanup
            # room.shutdown()  # if you implement one

            del self.rooms[room_name]
# =====================

room_manager = RoomManager()
next_id = 1

# =====================
# TCP
# =====================

def tcp_thread(conn):
    global next_id

    try:
        username = conn.recv(128).decode()
    except Exception as e:
        print("TCP recv failed during login", e)
        conn.close()
        return

    with clients_lock:
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

        except Exception as e:
            print("TCP thread error for client", client.username, e)
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
    last_broadcast_all = time.perf_counter()
    
    while True:
        # ---------------------------------
        # WAIT FOR PACKETS with short timeout (responsive but not busy-wait)
        # ---------------------------------
        readable, _, _ = select.select([udp], [], [], 0.005)  # 5ms timeout

        if readable:
            try:
                while True:  # drain all waiting packets
                    try:
                        data, addr = udp.recvfrom(1024)
                    except BlockingIOError:
                        break
                    except Exception as e:
                        # print("UDP recv error", e)
                        break

                    try:
                        ptype_val = struct.unpack("!B", data[:1])[0]
                    except struct.error:
                        continue

                    if ptype_val == PacketType.PING:
                        try:
                            cid, timestamp = struct.unpack(PING_FORMAT, data)[1:]
                        except struct.error:
                            continue

                        with clients_lock:
                            client = clients.get(cid)
                        if not client or not client.room:
                            continue

                        # PONG immediately - highest priority
                        pong = struct.pack(PONG_FORMAT, PacketType.PONG, timestamp)
                        client.last_seen = time.perf_counter()
                        try:
                            udp.sendto(pong, addr)
                        except Exception as e:
                            print("Failed to send pong", e)

                    elif ptype_val == PacketType.INPUT:
                        try:
                            _, cid, keys, dx, dy, timestamp = struct.unpack(CLIENT_PACK_FORMAT, data)

                        except struct.error:
                            continue

                        with clients_lock:
                            client = clients.get(cid)
                        if not client:
                            continue
                        room = client.room
                        if not room:
                            continue

                        client.udp_addr = addr
                        client.last_seen = time.perf_counter()


                        try:
                            client.ServerController.input_queue.append((keys, dx, dy))

                        except Exception as e:
                            print("Input controller error", e)

            except Exception as e:
                print("Packet processing error", e)

        # ---------------------------------
        # BROADCAST GAME STATE (fixed 60 Hz tick)
        # ---------------------------------
        SERVER_TICK = 1 / 60  # 60 Hz = ~16.67ms between broadcasts
        now = time.perf_counter()
        if now - last_broadcast_all > SERVER_TICK:
            try:
                with room_manager_lock:
                    rooms_copy = list(room_manager.rooms.values())

                for room in rooms_copy:
                    # broadcast all clients in this room to each other
                    for client in room.clients:
                        if not client.udp_addr:
                            continue
                        position = client.game_object.position
                        rotation = client.game_object.quaternion
                        velocity = client.game_object.Rigidbody.velocity

                        data = struct.pack(STATE_FORMAT, PacketType.STATE,
                                            client.id,
                                            position.x, position.y, position.z,
                                            rotation.w, rotation.x, rotation.y, rotation.z,
                                            velocity.x, velocity.y, velocity.z,
                                            )
                        room.broadcast(data, udp)  # broadcast to everyone

            except Exception as e:
                print("Broadcast error", e)

            last_broadcast_all = now
        try:
            with room_manager_lock:
                rooms_copy = list(room_manager.rooms.values())

            for room in rooms_copy:
                # broadcast all clients in this room to each other
                for client in room.clients:
                    if not client.udp_addr:
                        continue

                    queue = client.game_object.ClientHelper.messages_queue
                    if queue:
                        try:
                            udp.sendto(queue.pop(), client.udp_addr)
                        except Exception as e:
                            print("Failed to send update message from server", e)

            logout_queue = ClientHelper.logout_deque
            if logout_queue:
                try:
                    client = logout_queue.pop()
                    room = client.room
                    room.broadcast(dead_message(client.id), udp)
                    client.log_out()
                except Exception as e:
                    print(f"Failed to logout a player! id: {client.id} username: {client.username}", e)

        except Exception as e:
            print("Updating error", e)

def main():
    # start networking threads as daemons so they exit when main thread stops
    threading.Thread(target=tcp_server, daemon=True).start()
    threading.Thread(target=udp_server, daemon=True).start()

    print("Server running")
    try:
        # keep the main thread alive until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        # sockets will close automatically when program exits


if __name__ == "__main__":
    main()

