import hashlib
import hmac
import socket
import threading
import struct
import random
import string
import select
import ssl
import secrets
import time

from bereshit import Object, Vector3, Camera, Core
from MAP import server_map, server_game_object
from ClientHelper import ClientHelper
from ContentFilter import ContentFilter

from protocol import PacketType, PacketFormat, TICK, SESSION_TIMEOUT, SIGNATURE_SIZE

from concurrent.futures import ThreadPoolExecutor


class Tcp:
    HOST = "0.0.0.0"
    MAX_CLIENTS = 100

    # @staticmethod
    # def despawn(cid):
    #     return struct.pack(PacketFormat(PacketType.DESPAWN), PacketType.DESPAWN, cid)
    #
    # @staticmethod
    # def respawn(cid):
    #     return struct.pack(PacketFormat(PacketType.RESPAWN), cid)

    def __init__(self, room_manager, clients, clients_lock, udp):
        """Initialize TCP server with managers and client tracking."""
        self.udp = udp
        self.TCP_PORT = 5000
        self.UDP_PORT = 5001
        self.clients = clients
        self.clients_lock = clients_lock
        self.connections_lock = threading.Lock()
        self.ip_connections = {}
        self.MAX_PER_IP = 5
        self.room_manager = room_manager
        self.room_manager_lock = self.room_manager.room_manager_lock
        self.next_id = 1
        self.executor = ThreadPoolExecutor(max_workers=50)
        self.active_connections = 0
        self.pending_handshakes = 0
        self.MAX_HANDSHAKES = 20

    def create_play_rooms(self, num):
        """Create specified number of default game rooms."""
        for i in range(num):
            pwd = self.room_manager.create_room(pwd=str(i + 1))
            self.room_manager.add_default_room(pwd)

    def create_new_room(self, client, conn):
        """Create a new room for client and send confirmation."""
        pwd = self.room_manager.create_room(client)
        client.last_seen = time.perf_counter()
        if pwd:
            conn.send(f"created a room with this password {pwd}".encode())
        else:
            conn.send(b"EXISTS")



    def tcp_server(self):
        """Start SSL TCP server and listen for client connections."""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile="server.crt", keyfile="server.key")

        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        tcp_sock.bind((self.HOST, self.TCP_PORT))
        tcp_sock.listen(1024)  # larger backlog

        print(f"[TCP] Server listening on {self.HOST}:{self.TCP_PORT}")

        self.create_play_rooms(1)

        while True:
            try:
                conn, addr = tcp_sock.accept()
                conn.settimeout(5)
            except Exception:
                continue

            self.executor.submit(self.tcp_handshake_thread, conn, addr, context)

    def tcp_handshake_thread(self, conn, addr, context):
        """Handle TLS handshake and route client to thread pool."""
        ip = addr[0]

        # 🔒 Per-IP rate limiting
        with self.connections_lock:
            count = self.ip_connections.get(ip, 0)
            if count >= 5:  # max 5 connections per IP
                conn.close()
                return
            self.ip_connections[ip] = count + 1

        # 🚫 TLS HANDSHAKE LIMITER (NEW)
        with self.connections_lock:
            if self.pending_handshakes >= self.MAX_HANDSHAKES:
                conn.close()
                self.ip_connections[ip] -= 1
                if self.ip_connections[ip] <= 0:
                    del self.ip_connections[ip]
                return
            self.pending_handshakes += 1

        # 🔐 TLS handshake
        try:
            conn.settimeout(3)
            conn = context.wrap_socket(conn, server_side=True)
            conn.settimeout(None)
        except Exception:
            conn.close()
            with self.connections_lock:
                self.pending_handshakes -= 1
                self.ip_connections[ip] -= 1
                if self.ip_connections[ip] <= 0:
                    del self.ip_connections[ip]
            return

        # ✅ Handshake done → release slot
        with self.connections_lock:
            self.pending_handshakes -= 1

        # 🟢 Remove timeout after handshake
        conn.settimeout(None)

        # 🌐 Global connection limit
        with self.connections_lock:
            if self.active_connections >= self.MAX_CLIENTS:
                conn.close()
                self.ip_connections[ip] -= 1
                if self.ip_connections[ip] <= 0:
                    del self.ip_connections[ip]
                return
            self.active_connections += 1

        # 🧠 Optional: slow down under heavy load
        if self.active_connections > self.MAX_CLIENTS * 0.8:
            time.sleep(0.01)

        # 🚀 Handle client in thread pool
        def client_wrapper(conn, addr):
            try:
                self.tcp_thread(conn)
            finally:
                # 🔻 Cleanup when client disconnects
                ip = addr[0]
                with self.connections_lock:
                    self.active_connections -= 1
                    if ip in self.ip_connections:
                        self.ip_connections[ip] -= 1
                        if self.ip_connections[ip] <= 0:
                            del self.ip_connections[ip]
                try:
                    conn.close()
                except:
                    pass

        self.executor.submit(client_wrapper, conn, addr)

    def tcp_thread(self, conn):
        """Handle client TCP connection and process commands."""
        try:
            username = conn.recv(128).decode()
            i = 0
            while self.room_manager.usernames.get(username):
                username = f"{username}_{i}"
                i += 1
        except Exception as e:
            print("TCP recv failed during login", e)
            conn.close()
            return

        with self.clients_lock:
            cid = self.next_id
            self.next_id += 1
            client = Client(cid, username, conn)
            client.start_new_session()
            self.clients[cid] = client

        data = struct.pack(PacketFormat(PacketType.LOGIN), cid, client.token, client.secret)
        conn.send(data)
        conn.settimeout(None)
        while True:
            try:
                data = conn.recv(256).decode()
                if not data:
                    break

                cmd = data.split()

                if cmd[0] == "CREATE":
                    self.create_new_room(client, conn)

                elif cmd[0] == "JOIN":
                    ok = self.room_manager.join_room(cmd[1], client)
                    conn.send(b"JOINED" if ok else b"FAILED")

                elif cmd[0] == "find_room":
                    conn.send(b"1")

                elif cmd[0] == "logout":
                    with self.clients_lock:
                        if cid in self.clients:
                            self.clients[cid].log_out()
                            self.clients.pop(cid, None)

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
                        client.room.broadcast_udp(b'', self.udp, PacketType.RESPAWN)
                    else:
                        conn.send(b"FAILED")

                elif cmd[0] == "despawn":
                    if client.room:
                        client.game_object.destroy()
                        conn.send(b"despawned")
                        client.room.broadcast_udp(b'', self.udp, PacketType.DESPAWN)
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
                    if client.room:
                        client.send_chat(msg, sender=client)
            except Exception as e:
                print("TCP thread error for client", client.username, e)
                break

        conn.close()


class Udp:
    # @staticmethod
    # def despawn(cid):
    #     return struct.pack(SPAWN_FORMAT, PacketType.DESPAWN, cid)

    @staticmethod
    def verify_signature(data, received_signature, secret):
        """Verify HMAC signature to ensure packet authenticity."""
        expected_signature = hmac.new(secret, data, hashlib.sha256).digest()

        return hmac.compare_digest(expected_signature, received_signature)

    def __init__(self, room_manager, clients, clients_lock):
        """Initialize UDP server for game state and input handling."""
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.bind(("0.0.0.0", 5001))
        self.clients = clients
        self.clients_lock = clients_lock
        self.room_manager = room_manager
        self.room_manager_lock = self.room_manager.room_manager_lock

        # VERY IMPORTANT
        self.udp.setblocking(False)

    def movement(self, raw_data, addr):
        """Process player movement input from UDP packet."""
        data_bytes = raw_data[:-SIGNATURE_SIZE]
        received_sig = raw_data[-SIGNATURE_SIZE:]
        data = struct.unpack( PacketFormat(PacketType.HEADER) + PacketFormat(PacketType.INPUT) , data_bytes)[1:]
        cid, token, seq, keys, dx, dy, timestamp = data

        with self.clients_lock:
            client = self.clients.get(cid)
        if not client:
            return
        room = client.room
        if not room:
            return

        if not client.verify_token(token):
            print("bad token")
            return

        if not Udp.verify_signature(data_bytes, received_sig, client.secret):
            print("Invalid signature")
            return

        if not client.verify_seq(seq):
            print("bad seq")
            return

        client.update_seq(seq)

        client.udp_addr = addr
        client.last_seen = time.perf_counter()

        try:
            client.ServerController.input_queue.append((keys, dx, dy))

        except Exception as e:
            print("Input controller error", e)

    def pong(self, raw_data, addr):
        """Send pong response to client ping request."""
        data_bytes = raw_data[:-SIGNATURE_SIZE]
        received_sig = raw_data[-SIGNATURE_SIZE:]
        cid, token, seq, timestamp = struct.unpack(PacketFormat(PacketType.HEADER) + PacketFormat(PacketType.PING), data_bytes)[1:]

        with self.clients_lock:
            client = self.clients.get(cid)
        if not client:
            return
        if not client.verify_token(token):
            return
        if not Udp.verify_signature(data_bytes, received_sig, client.secret):
            print("Invalid signature")
            return

        pong = struct.pack(PacketFormat(PacketType.PONG), PacketType.PONG, timestamp)
        client.last_seen = time.perf_counter()
        try:
            self.udp.sendto(pong, addr)
        except Exception as e:
            print("Failed to send pong", e)

    def udp_server(self):
        """Start UDP server to handle player state and input updates."""
        last_broadcast_all = time.perf_counter()

        while True:
            # ---------------------------------
            # WAIT FOR PACKETS with short timeout (responsive but not busy-wait)
            # ---------------------------------
            readable, _, _ = select.select([self.udp], [], [], 0.005)  # 5ms timeout

            if readable:
                try:
                    while True:  # drain all waiting packets
                        try:
                            data, addr = self.udp.recvfrom(1024)
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
                                self.pong(data, addr)
                            except struct.error:
                                print("could not receive ping")
                                continue

                        elif ptype_val == PacketType.INPUT:
                            try:
                                self.movement(data, addr)
                            except struct.error:
                                print("bad player input Packet")
                                continue
                except Exception as e:
                    print("Packet processing error", e)

            SERVER_TICK = 1 / 60  # 60 Hz = ~16.67ms between broadcasts
            now = time.perf_counter()
            if now - last_broadcast_all > SERVER_TICK:
                try:
                    with self.room_manager_lock:
                        rooms_copy = list(self.room_manager.rooms.values())
                    self.broadcast(rooms_copy)
                    self.token_update(rooms_copy)
                except Exception as e:
                    print("Broadcast error", e)

                last_broadcast_all = now
            try:
                self.logout()
                self.shoot()
                # self.send_chat()
            except Exception as e:
                print("logout error", e)

    def broadcast(self, rooms):
        """Broadcast current game state to all clients in rooms."""
        for room in rooms:
            for client in room.clients:
                if not client.udp_addr:
                    continue

                position = client.game_object.position
                rotation = client.game_object.quaternion
                velocity = client.game_object.Rigidbody.velocity

                data = (position.x, position.y, position.z, rotation.w, rotation.x, rotation.y, rotation.z, velocity.x,
                        velocity.y, velocity.z)

                room.broadcast_udp(data, self.udp, PacketType.STATE, id=client.id)  # broadcast to everyone

    def token_update(self, rooms):
        """Refresh authentication tokens for active clients."""
        for room in rooms:
            for client in room.clients:
                if time.perf_counter() - client.session_time > 60 * 5:  # 5 minutes
                    client.start_new_session()
                    msg = client.token + client.secret
                    print(client.token)
                    client.tcp_addr.send(msg)


    def shoot(self):
        """Send queued game events (attacks) to clients."""
        with self.room_manager_lock:
            rooms_copy = list(self.room_manager.rooms.values())

        for room in rooms_copy:
            for client in room.clients:
                if not client.udp_addr:
                    continue

                queue = client.game_object.ClientHelper.messages_queue
                if queue:
                    try:
                        msg, type = queue.pop()
                        msg = client.pack_data(type, msg)
                        self.udp.sendto(msg, client.udp_addr)
                    except Exception as e:
                        print("Failed to send update message from server", e)


    def logout(self):
        """Process client logouts and clean up disconnected players."""
        return  # this is not in use right now
        with self.room_manager_lock:
            rooms_copy = list(self.room_manager.rooms.values())

        for room in rooms_copy:
            # broadcast all clients in this room to each other
            for client in room.clients:
                if not client.udp_addr:
                    continue

                queue = client.game_object.ClientHelper.messages_queue
                if queue:
                    try:
                        self.udp.sendto(queue.pop(), client.udp_addr)
                    except Exception as e:
                        print("Failed to send update message from server", e)

        logout_queue = ClientHelper.logout_deque
        if logout_queue:
            try:
                client = logout_queue.pop()
                room = client.room
                room.broadcast_udp(Udp.despawn(client.id), self.udp)
                client.log_out()
            except Exception as e:
                print(f"Failed to logout a player! id: {client.id} username: {client.username}", e)


class Server:
    def __init__(self):
        """Initialize server with client tracking structures."""
        self.clients = {}
        self.clients_lock = threading.Lock()

    def run(self):
        """Start TCP and UDP servers in background threads."""
        manager = RoomManager()
        udp = Udp(manager, self.clients, self.clients_lock)
        tcp = Tcp(manager, self.clients, self.clients_lock, udp.udp)
        # start networking threads as daemons so they exit when main thread stops
        threading.Thread(target=tcp.tcp_server, daemon=True).start()
        threading.Thread(target=udp.udp_server, daemon=True).start()

        print("Server running")
        try:
            # keep the main thread alive until interrupted
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down server...")
            # sockets will close automatically when program exits


class Client:
    def __init__(self, id, username, tcp_addr):
        """Initialize client session with ID, name, and TCP connection."""
        self.__id = id
        self.__token = None
        self.__secret = None
        self.__seq = 0
        self.__session_time = time.process_time()
        self.username = username
        self.room = None
        self.udp_addr = None
        self.tcp_addr = tcp_addr
        self.game_object = server_game_object(username, self)
        self.last_seen = time.perf_counter()
        self.ServerController = self.game_object.ServerController

    @property
    def secret(self):
        """Get the session secret."""
        return self.__secret

    def log_out(self):
        """Remove client from room and clean up resources."""
        if self.room:
            self.room.remove_client(self)
        del self

    def _generate_token(self):
        """Generate cryptographically secure random token."""
        token = secrets.token_bytes(16)
        return token

    def _generate_session(self):
        """Generate token and secret for new session."""
        return self._generate_token(), secrets.token_bytes(32)

    def verify_token(self, token):
        """Check if token is valid and session has not timed out."""
        if hmac.compare_digest(self.__token, token):
            if time.process_time() - self.__session_time < SESSION_TIMEOUT:
                return True
        return False

    def verify_seq(self, seq):
        """Check if sequence number is valid."""
        return self.__seq <= seq

    def update_seq(self, seq):
        """Update the sequence number to latest value."""
        self.__seq = seq

    @property
    def session_time(self):
        """Get session start timestamp."""
        return self.__session_time

    def start_new_session(self):
        """Generate new token and secret for session refresh."""
        self.__token, self.__secret = self._generate_session()
        self.__seq = 0
        self.__session_time = time.perf_counter()

    @property
    def id(self):
        """Get the client ID."""
        return self.__id

    @property
    def token(self):
        """Get the authentication token."""
        return self.__token

    @property
    def seq(self):
        """Get the current sequence number."""
        # self += 1
        return self.__seq

    def build_signature(self, data):
        """Generate HMAC-SHA256 signature for packet data."""
        return hmac.new(self.__secret, data, hashlib.sha256).digest()

    def pack_data(self, type, data, id=None):
        """Pack data with header, payload, and signature into packet format."""
        id = self.id if not id else id
        fmt = PacketFormat(PacketType.HEADER) + PacketFormat(type)

        if isinstance(data, tuple) or (isinstance(data, bytes) and len(data) == 0):
            msg = struct.pack(fmt, type, id, self.token, self.seq, *data)
        else:
            msg = struct.pack(fmt, type, id, self.token, self.seq, data)
        return msg + self.build_signature(msg)

    def send_chat(self, msg, sender=None):
        """Send filtered chat message to other clients in room."""
        try:
            if not Room.chat_filter.is_message_clean(msg):
                msg = Room.chat_filter.censor(msg)
            msg = "CHAT " + self.username + ": " + msg
            self.room.broadcast_tcp(msg.encode(), sender=sender)
        except Exception as e:
            print("Failed to send update message from server", e)
class Room:
    chat_filter = ContentFilter()

    def __init__(self, password, room_manager):
        """Initialize game room with password and physics world."""
        self.password = password
        self.clients = []
        self.room_manager = room_manager
        camera = Object(name="camera", position=Vector3(0, 10, 0), rotation=Vector3(90, 0, 0)).add_component(Camera())
        self.Camera = camera
        self.last_broadcast = time.perf_counter()

    def add_client(self, client):
        """Add client to room and set room reference."""
        if client not in self.clients:
            self.clients.append(client)
            # self.Camera.add_child(client.game_object)
            client.room = self

    def remove_client(self, client):
        """Remove client from room and clean up empty rooms."""
        if client in self.clients:
            self.clients.remove(client)
            if client.game_object:
                client.game_object.destroy()

            # Clear the client's room reference
            client.room = None
        if not self.clients and not self.room_manager.is_default_room(self):
            # no more players: shut down the physics world
            try:
                if hasattr(self.Camera, 'World'):
                    self.Camera.World.Exit()
                    print(f"Removing room: {self.password}")
            except Exception:
                pass
            # remove from manager
            self.room_manager.remove_room(self.password)

    def broadcast_udp(self, data, udp, type, id=None):
        """Send UDP packet to all clients in room."""
        for c in self.clients:
            if c.udp_addr:
                udp.sendto(c.pack_data(type, data, id=id), c.udp_addr)

    def broadcast_tcp(self, data, sender=None):
        """Send TCP message to all clients except sender."""
        for client in self.clients:
            if client != sender:
                client.tcp_addr.send(data)




class RoomManager:
    def __init__(self):
        """Initialize room manager for creating and tracking rooms."""
        self.rooms = {}
        self.usernames = {}
        self._default_rooms = []
        self.room_manager_lock = threading.Lock()

    @staticmethod
    def generate_password():
        """Generate random 6-character password for room."""
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))

    def create_room(self, owner=None, pwd=None):
        """Create new game room and start physics simulation."""
        with self.room_manager_lock:
            if not pwd:
                pwd = self.generate_password()
            # pwd = "0" # temp for testing

            if pwd in self.rooms:
                return None

            room = Room(pwd, self)
            self.rooms[pwd] = room
            if owner:
                owner.last_seen = time.perf_counter()
                room.add_client(owner)  # auto join

            threading.Thread(target=Core.run, args=([room.Camera] + server_map(),),
                             kwargs={"Render": False, "tick": TICK}, daemon=True).start()

            return pwd

    def join_room(self, pwd, client):
        """Add client to existing room by password."""
        with self.room_manager_lock:
            room = self.rooms.get(pwd)
            if not room:
                return False

            client.last_seen = time.perf_counter()
            room.add_client(client)
            self.usernames[client.username] = True
            return True

    def remove_room(self, room_password):
        """Remove empty room from manager."""
        with self.room_manager_lock:
            room = self.rooms.get(room_password)
            if not room:
                return

            print(f"Removing room: {room_password}")

            # Optional: stop game loop / cleanup
            # room.shutdown()  # if you implement one

            del self.rooms[room_password]

    def add_default_room(self, room):
        """Mark room as default (persistent) room."""
        self._default_rooms.append(self.rooms[room])

    def get_default_room(self):
        """Get a default room (not implemented)."""
        return  # to do

    def is_default_room(self, room):
        """Check if room is a default persistent room."""
        return room in self._default_rooms


if __name__ == "__main__":
    server = Server()
    server.run()
