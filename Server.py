import socket
import threading
import struct
import random
import string
import select
import ssl

from bereshit import Object, Vector3, Camera, Core
from MAP import server_map, server_game_object
from ClientHelper import ClientHelper
import time

from protocol import PacketType, CLIENT_PACK_FORMAT, PING_FORMAT, PONG_FORMAT, STATE_FORMAT, TICK, SPAWN_FORMAT


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
def despawn(cid):
    return struct.pack(SPAWN_FORMAT, PacketType.DESPAWN, cid)

def respawn(cid):
    return struct.pack(SPAWN_FORMAT, PacketType.RESPAWN, cid)



class Client:
    def __init__(self, cid, username, tcp_addr):
        self.id = cid
        self.username = username
        self.room = None
        self.udp_addr = None
        self.tcp_addr = tcp_addr
        self.game_object = server_game_object(username, self)
        self.last_seen = time.perf_counter()
        self.ServerController = self.game_object.ServerController

    def log_out(self):
        self.room.remove_client(self)
class Room:
    def __init__(self, password, room_manager):
        self.password = password
        self.clients = []
        self.room_manager = room_manager
        camera = Object(name="camera", position=Vector3(0,10,0), rotation=Vector3(90,0,0)).add_component(Camera())
        self.Camera = camera
        self.last_broadcast = time.perf_counter()

    def add_client(self, client):
        if client not in self.clients:
            self.clients.append(client)
            # self.Camera.add_child(client.game_object)
            client.room = self

    def remove_client(self, client):
        if client in self.clients:
            self.clients.remove(client)
            if client.game_object:
                client.game_object.destroy()

            # Clear the client's room reference
            client.room = None
        if not self.clients and not room_manager.is_default_room(self):
            # no more players: shut down the physics world
            try:
                if hasattr(self.Camera, 'World'):
                    self.Camera.World.Exit()
                    print(f"Removing room: {self.password}")
            except Exception:
                pass
            # remove from manager
            self.room_manager.remove_room(self.password)



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
        self._default_rooms = []


    def generate_password(self):
        return ''.join(random.choice(string.ascii_letters+string.digits) for _ in range(6))

    def create_room(self, owner=None, pwd=None):
        with room_manager_lock:
            if not pwd:
                pwd = self.generate_password()
            # pwd = "0" # temp for testing

            if pwd in self.rooms:
                return None

            room = Room(pwd, room_manager)
            self.rooms[pwd] = room
            if owner:
                owner.last_seen = time.perf_counter()
                room.add_client(owner)  # auto join


            threading.Thread(target=Core.run, args=([room.Camera] + server_map(),), kwargs={"Render": False, "tick": TICK}, daemon=True).start()

            return pwd


    def join_room(self, pwd, client):
        with room_manager_lock:
            room = self.rooms.get(pwd)
            if not room:
                return False

            client.last_seen = time.perf_counter()
            room.add_client(client)
            return True

    def remove_room(self, room_password):
        with room_manager_lock:
            room = self.rooms.get(room_password)
            if not room:
                return

            print(f"Removing room: {room_password}")

            # Optional: stop game loop / cleanup
            # room.shutdown()  # if you implement one

            del self.rooms[room_password]

    def add_default_room(self, room):
        self._default_rooms.append(self.rooms[room])

    def get_default_room(self):
        return # to do
    def is_default_room(self, room):
        return room in self._default_rooms
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
        client = Client(cid, username, conn)
        clients[cid] = client

    conn.send(f"LOGIN {cid}".encode())

    while True:
        try:
            data = conn.recv(256).decode()
            if not data:
                break

            cmd = data.split()

            if cmd[0] == "CREATE":
                pwd = room_manager.create_room(client)
                client.last_seen = time.perf_counter()
                if pwd:
                    conn.send(f"created a room with this password {pwd}".encode())
                else:
                    conn.send(b"EXISTS")

            elif cmd[0] == "JOIN":
                ok = room_manager.join_room(cmd[1], client)
                conn.send(b"JOINED" if ok else b"FAILED")

            elif cmd[0] == "find_room":
                conn.send(b"1")

            elif cmd[0] == "logout":
                with clients_lock:
                    if cid in clients:
                        # del clients[cid]
                        clients[cid].log_out()

                conn.send(b"LOGGED_OUT")
                conn.close()
                break

            elif cmd[0] == "respawn":
                if client.room:
                    client.last_seen = time.perf_counter()
                    client.game_object.ServerController.total_pitch = 0
                    client.game_object.ServerController.total_yaw = 0
                    client.game_object.Player.respawn()
                    client.room.Camera.add_child(client.game_object)
                    conn.send(b"respawned")
                    client.room.broadcast(respawn(cid), udp)
                else:
                    conn.send(b"FAILED")

            elif cmd[0] == "despawn":
                if client.room:
                    client.game_object.destroy()
                    conn.send(b"despawned")
                    client.room.broadcast(despawn(client.id), udp)
                else:
                    conn.send(b"FAILED")

            elif cmd[0] == "leave":
                if client.room:
                    client.log_out()
                    conn.send(b"left")
                else:
                    conn.send(b"FAILED")

            elif cmd[0] == "CHAT":
                msg = cmd[1]
                for c in client.room.clients:
                    if c != client:
                        try:
                            c.tcp_addr.sendall(msg.encode())
                        except Exception as e:
                           print(f"could not send msg {e}")
        except Exception as e:
            print("TCP thread error for client", client.username, e)
            break

    conn.close()

def tcp_server():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind((HOST, TCP_PORT))
    tcp_sock.listen()
    create_play_rooms(1)
    while True:
        conn, _ = tcp_sock.accept()

        conn = context.wrap_socket(conn, server_side=True)
        threading.Thread(target=tcp_thread, args=(conn, )).start()


def create_play_rooms(num):
    for i in range(num):
        pwd = room_manager.create_room(pwd=str(i+1))
        room_manager.add_default_room(pwd)

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
                    room.broadcast(despawn(client.id), udp)
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

