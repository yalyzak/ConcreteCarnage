# client.py
import ast
import hashlib
import hmac
import random
import socket
import struct
import time
import select
import ssl
from collections import deque

from bereshit import Vector3, Object
from MAP import client_game_object

from protocol import PacketType, PacketFormat, TICK, SESSION_TIMEOUT, SIGNATURE_SIZE, SIGNATURE_FORMAT


class Client:

    @staticmethod
    def verify_signature(data, received_signature, secret):
        """Verify HMAC signature to ensure data authenticity."""
        """Verify HMAC signature to ensure data authenticity."""
        expected_signature = hmac.new(secret, data, hashlib.sha256).digest()
        return hmac.compare_digest(expected_signature, received_signature)

    def __init__(self, name="", ip="127.0.0.1"):
        """Initialize client with name and server IP address."""
        self.name = name
        self.id = None
        self.__token = None
        self.__secret = None
        self.logged_in = False
        self.server_ip = ip
        self.__seq = 0
        self.__max_players = 5

        context = ssl.create_default_context()
        self.context = ssl._create_unverified_context()

        self.tcp = self.connect()
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.udp.setblocking(False)
        self.udp.settimeout(0.002)  # seconds

        self.tcp.setblocking(False)
        self.tcp.settimeout(0.002)

        self.last_ping_time = 0
        self.wait = False

        self.players = Object(size=Vector3(0, 0, 0), name="players")

        self.chat_queue = deque(maxlen=6)

        self.switch = {
            PacketType.PONG: self.handle_pong,
            PacketType.STATE: self.handle_state,
            PacketType.RESPAWN: self.handle_respawn,
            PacketType.DESPAWN: self.handle_despawn,
            PacketType.DAMAGE: self.handle_damage,

        }

    @property
    def token(self):
        """Get the authentication token."""
        return self.__token

    def _set_token(self, value):
        """Set the authentication token."""
        self.__token = value
    
    def _new_session(self, token, secret):
        """Initialize a new session with token and secret."""
        self.__token = token
        self.__secret = secret
        self.__seq = 0

    @property
    def secret(self):
        """Get the session secret."""
        return self.__secret

    def _set_secret(self, value):
        """Set the session secret."""
        self.__secret = value

    @property
    def seq(self):
        """Get the current sequence number."""
        # self.__seq += 1
        return self.__seq

    def attach(self, owner_object):
        """Attach client to owner object and get input queue."""
        self.input = owner_object.PlayerController.input_queue

    def connect(self):
        """Create and return SSL-wrapped TCP socket connection."""
        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp = self.context.wrap_socket(raw, server_hostname="localhost")
        return tcp

    def Update(self, dt):
        """Update client state, handle input and network communication."""
        if self.input:
            bools, dx, dy = self.input.popleft()
            self.send_input(bools, dx, dy, dt)
        if time.perf_counter() - self.last_ping_time > 1:
            if not self.wait:
                self.send_ping()

        self.receive_input()
        self.receive_tcp()


    def Start(self):
        """Initialize client and add players object to world."""
        self.parent.World.add_object(self.players)
        self.Active = True
        # self.login()
        # pwd = self.create_room()
        # self.join_room("0") # temp for testing

    def login(self):
        """Authenticate with server and establish session."""
        if not self.logged_in:
            try:
                self.tcp = self.connect()
                self.wait = False
                self.tcp.connect((self.server_ip, 5000))
                self.tcp.send(self.name.encode())

                msg = self.tcp.recv(128)

                parts = struct.unpack(PacketFormat(PacketType.LOGIN), msg)

                if len(parts) < 3:
                    raise ValueError(f"Invalid login response: {msg}")

                self.id = int(parts[0])

                # keep as BYTES (good for crypto later)
                self._set_token(parts[1])
                self._set_secret(parts[2])

                self.logged_in = True
            except Exception as e:
                print("Login failed", e)
                raise

    def logout(self):
        """Close connection and log out from server."""
        if self.logged_in:
            try:
                # Optional: notify the server that this client is logging out
                self.tcp.send(b"logout")
                response = self.tcp.recv(128).decode()

                # Close the socket
                self.tcp.close()

                print(response)
                self.logged_in = False
            except Exception as e:
                print("Logout failed:", e)

    def create_room(self):
        """Create a new game room on the server."""
        self.tcp.send(b"CREATE")  #
        response = self.tcp.recv(128).decode()
        # Extract password from response
        if "password" in response:
            pwd = response.split()[-1]
            return pwd
        return None

    def join_room(self, pwd):
        """Join an existing room with given password."""
        self.tcp.send(f"JOIN {pwd}".encode())
        response = self.tcp.recv(128).decode()
        print(response)
        return response == "JOINED"

    def find_room(self):
        """Find an available room on the server."""
        self.tcp.send(b"find_room")
        response = int(self.tcp.recv(128).decode())
        return response

    def leave_room(self):
        """Leave the current room."""
        self.tcp.send(b"leave")
        response = self.tcp.recv(128).decode()
        print(response)

    def respawn(self):
        """Request respawn from server and reset player orientation."""
        self.tcp.send(b"respawn")
        self.parent.PlayerController.total_yaw = 0
        self.parent.PlayerController.total_pitch = 0
        self.parent.Player.respawn()
        response = self.tcp.recv(128).decode()
        print(response)

    def despawn(self):
        """Request despawn from server."""
        self.tcp.send(b"despawn")
        response = self.tcp.recv(128).decode()
        print(response)
        # Extract password from response
        if "password" in response:
            pwd = response.split()[-1]
            return pwd
        return None

    def verify_token(self, token):
        """Check if provided token matches client's token."""
        return hmac.compare_digest(self.__token, token)

    def verify_seq(self, seq):
        """Check if sequence number is valid."""
        return self.__seq <= seq

    def send_chat(self, msg):
        """Send chat message to server."""
        self.tcp.send(f"CHAT {msg}".encode())

    def send_ping(self):
        """Send ping packet to measure latency."""
        now = time.perf_counter()
        self.wait = True

        self.udp.sendto(self.pack_data(PacketType.PING, now), (self.server_ip, 5001))
        self.last_ping_time = now

    def send_input(self, keys, dx, dy, dt):
        """Send player input (movement, mouse delta, timestamp) to server."""
        mask = 0
        for i, pressed in enumerate(keys):
            if pressed:
                mask |= (1 << i)
        data = (mask, dx, dy, dt)
        self.udp.sendto(self.pack_data(PacketType.INPUT, data), (self.server_ip, 5001))

    def pack_data(self, type, data):
        """Pack data with header, payload, and signature into packet format."""
        fmt = PacketFormat(PacketType.HEADER) + PacketFormat(type)
        if isinstance(data, tuple):
            msg = struct.pack(fmt, type, self.id, self.token, self.seq, *data)
        else:
            msg = struct.pack(fmt, type, self.id, self.token, self.seq, data)
        return msg + self.build_signature(msg)

    def unpack_data(self, type, raw_data):
        """Unpack packet into components: id, token, seq, data, and signature."""
        fmt = PacketFormat(PacketType.HEADER) + PacketFormat(type) + SIGNATURE_FORMAT

        unpacked = struct.unpack(fmt, raw_data)

        id = unpacked[1]
        token = unpacked[2]
        seq = unpacked[3]

        data = unpacked[4:-1]

        return id, token, seq, data, raw_data[:-SIGNATURE_SIZE], raw_data[-SIGNATURE_SIZE:]

    def position_correction(self, game_pos, server_pos, game_vel, server_vel):
        """Correct client position and velocity based on server state."""
        # --- Settings ---
        snap_distance = 1.8  # if too far away -> teleport
        lerp_speed = 0.5  # smoothing speed
        velocity_correction = 0.9  # how much velocity to blend

        # --- Position correction ---
        distance = (server_pos - game_pos).magnitude()

        if distance > snap_distance:
            # Large error -> snap directly
            self.parent.position = server_pos
            self.parent.Rigidbody.velocity = server_vel
        else:
            # Small error -> smooth correction
            self.parent.position = Vector3.Lerp(
                game_pos,
                server_pos,
                1 / 60 * lerp_speed
            )

        # --- Velocity correction ---
        self.parent.Rigidbody.velocity = Vector3.Lerp(
            game_vel,
            server_vel,
            velocity_correction
        )

    def handle_pong(self, raw_data):
        """Process pong response and update ping display."""
        try:
            ts = struct.unpack(PacketFormat(PacketType.PONG), raw_data)[1]
        except struct.error:
            print("Bad pong packet")
            return
        self.wait = False

        ping = (time.perf_counter() - ts) * 1000
        self.parent.HomeUI.updatePing(round(ping, 2))
        # print(f"Ping: {ping:.2f} ms")

    def handle_respawn(self, id, _):
        """Handle player respawn event from server."""
        try:
            if id == self.id:
                self.parent.Player.respawn()
            else:
                player = self.players.search(id)
                if player:
                    player.Player.respawn()
        except:
            print("Bad death packet")

    def handle_despawn(self, id, _):
        """Handle player despawn event from server."""
        try:
            if id == self.id:
                self.parent.Player.despawn()
            else:
                player = self.players.search(id)
                if player:
                    player.Player.despawn()
        except:
            print("Bad death despawn")

    def handle_damage(self, id, data):
        """Handle damage packet and update player health."""
        try:
            hp = data[0]
        except struct.error:
            print("Bad damage packet")
            return
        self.parent.Player.Hit(hp)

    def handle_state(self, id, data):
        """Update player position, rotation, and velocity from server state."""
        try:
            px, py, pz, rw, rx, ry, rz, vx, vy, vz = data
        except struct.error:
            print("Bad state packet")
            return

        server_pos = Vector3(px, py, pz)
        server_vel = Vector3(vx, vy, vz)
        if id == self.id:
            game_pos = self.parent.position
            game_vel = self.parent.Rigidbody.velocity
            self.position_correction(game_pos, server_pos, game_vel, server_vel)
        else:
            player = self.players.search(id)
            if player:
                player.position = server_pos
                player.Rigidbody.velocity = server_vel
            else:  # tobe removed
                if len(self.players.children) < self.__max_players:
                    self.players.add_child(client_game_object(id, server_pos, server_vel))
                    print("new player joined")

    def handle_packet(self, data):
        """Route incoming packet to appropriate handler based on type."""
        try:
            ptype = struct.unpack("!B", data[:1])[0]
        except struct.error:
            print("Malformed packet received (too short)")
            return
        if ptype == PacketType.PONG:
            self.handle_pong(data)
        else:
            id, token, seq, data, data_bytes, signature = self.unpack_data(ptype, data)
            if not self.verify_token(token):
                print("bad token "+ token)
                return

            if not self.verify_signature(data_bytes, signature, self.__secret):
                print("Invalid signature")
                return

            # if not self.verify_seq(seq):
            #     print("bad seq", self.seq)
            #     return

            self.switch.get(ptype)(id, data)

        # if ptype == PacketType.PONG:
        #
        # elif ptype == PacketType.STATE:
        #     self.state(data)
        # elif ptype == PacketType.DAMAGE:
        #     try:
        #         hp = struct.unpack(DAMAGE_FORMAT, data)[1]
        #     except struct.error:
        #         print("Bad damage packet")
        #         return
        #     self.parent.Player.Hit(hp)
        #
        # elif ptype == PacketType.DESPAWN:
        #
        # elif ptype == PacketType.RESPAWN:
        #     try:
        #         player_id = struct.unpack(PacketFormat(PacketType.RESPAWN), data)[1]
        #         if player_id == self.id:
        #             self.parent.Player.respawn()
        #         else:
        #             player = self.players.search(player_id)
        #             if player:
        #                 player.Player.respawn()
        #     except:
        #         print("Bad death packet")
        # else:
        #     print("Unknown packet", ptype)

    def receive_input(self):
        """Receive and process UDP packets from server."""
        try:
            ready, _, _ = select.select([self.udp], [], [], 0.0002)
        except Exception as e:
            print("select error on UDP socket", e)
            return
        while True:
            try:
                data, _ = self.udp.recvfrom(1024)
                self.handle_packet(data)
            except BlockingIOError:
                break
            except Exception as e:
                # print("UDP receive error", e)
                break

    def receive_chat(self):
        """Receive chat messages from server via TCP."""
        if not self.logged_in:
            return

        try:
            ready, _, _ = select.select([self.tcp], [], [], 0)
            if not ready:
                return

            data = self.tcp.recv(1024)

            if not data:
                print("TCP closed")
                return
            return data

        except BlockingIOError:
            pass

    def handel_tcp(self, msg):
        """Process incoming TCP messages (chat or session updates)."""
        if msg:
            cmd = msg.split()

            if cmd[0] == b"CHAT":
                self.chat_queue.append(msg[5:].decode())
            else:
                token = msg[:16]
                secret = msg[16:]
                self._new_session(token, secret)

    def receive_tcp(self):
        """Receive and process TCP messages from server."""
        if not self.logged_in:
            return

        try:
            ready, _, _ = select.select([self.tcp], [], [], 0)
            if not ready:
                return

            data = self.tcp.recv(1024)

            if not data:
                print("TCP closed")
                return

            self.handel_tcp(data)

        except BlockingIOError:
            pass


    def next_seq(self):
        """Get next sequence number."""
        # self.__seq += 1
        return self.__seq

    def build_signature(self, data):
        """Generate HMAC-SHA256 signature for packet data."""
        return hmac.new(self.__secret, data, hashlib.sha256).digest()


# =====================
if __name__ == "__main__":
    c = Client("Player1")
    c.login()  # test login
    psw = c.find_room()  # test find room
    c.join_room(psw)     # test join room
    time.sleep(1)

    start = time.perf_counter()

    while True:  # test ping
        c.send_ping()
        c.receive_tcp()
        time.sleep(1)

    c.logout()  # test logout
