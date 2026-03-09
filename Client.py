# client.py
import random
import socket
import struct
import time
import select
import ssl

from bereshit import Vector3, Object, BoxCollider, Rigidbody

from protocol import PacketType, CLIENT_PACK_FORMAT, PING_FORMAT, PONG_FORMAT, STATE_FORMAT, DAMAGE_FORMAT, DEATH_FORMAT

from Player import GamePlayer

class Client:

    def __init__(self, name, ip = "127.0.0.1"):
        self.name = name
        self.id = None

        self.server_ip = ip

        context = ssl.create_default_context()
        context = ssl._create_unverified_context()
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp = context.wrap_socket(self.tcp, server_hostname="localhost")
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.udp.setblocking(False)
        self.udp.settimeout(0.002)  # seconds

        self.last_ping_time = 0
        self.wait = False

        self.players = Object(size=Vector3(0,0,0), name="players")
    def attach(self, owner_object):
        self.input = owner_object.PlayerController.input_queue

    def Update(self, dt):
        if self.input:
            bools, dx, dy = self.input.popleft()
            self.send_input(bools, dx, dy, dt)
        if time.perf_counter() - self.last_ping_time > 1:
            if not self.wait:
                self.send_ping()

        self.receive_input()
    def Start(self):
        self.parent.World.add_object(self.players)
        self.login()
        pwd = self.create_room()
        # self.join_room("0") # temp for testing
    def login(self):
        try:
            self.tcp.connect((self.server_ip, 5000))
            self.tcp.send(self.name.encode())

            msg = self.tcp.recv(128).decode()
            self.id = int(msg.split()[1])
            print("id", self.id)
        except Exception as e:
            print("Login failed", e)
            raise

    def create_room(self):
        self.tcp.send(b"CREATE")
        response = self.tcp.recv(128).decode()
        print(response)
        # Extract password from response
        if "password" in response:
            pwd = response.split()[-1]
            return pwd
        return None

    def join_room(self, pwd):
        self.tcp.send(f"JOIN {pwd}".encode())
        response = self.tcp.recv(128).decode()
        print(response)
        return response == "JOINED"

    def Connect(self, room, username):
        # Dummy method for UI
        return True

    def send_input(self, keys, dx, dy, dt):
        mask = 0
        for i, pressed in enumerate(keys):
            if pressed:
                mask |= (1 << i)

        packet = struct.pack(
            CLIENT_PACK_FORMAT,
            PacketType.INPUT,
            self.id,
            mask,
            dx,
            dy,
            dt
        )

        self.udp.sendto(packet, (self.server_ip, 5001))
    @staticmethod
    def game_object(player_id, server_pos, server_vel):
         return Object(name=player_id, position=server_pos).add_component(
            [BoxCollider(),
             Rigidbody(Freeze_Rotation=Vector3(1, 1, 1), velocity=server_vel),
             GamePlayer()
             ])

    def position_correction(self, game_pos, server_pos, game_vel, server_vel):


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
                1/60 * lerp_speed
            )

        # --- Velocity correction ---
        self.parent.Rigidbody.velocity = Vector3.Lerp(
            game_vel,
            server_vel,
            velocity_correction
        )
    def handle_packet(self, data):
        try:
            ptype = struct.unpack("!B", data[:1])[0]
        except struct.error:
            print("Malformed packet received (too short)")
            return

        if ptype == PacketType.PONG:
            try:
                ts = struct.unpack(PONG_FORMAT, data)[1]
            except struct.error:
                print("Bad pong packet")
                return
            self.wait = False

            ping = (time.perf_counter() - ts) * 1000
            # print(f"Ping: {ping:.2f} ms")

        elif ptype == PacketType.STATE:
            try:
                player_id, px, py, pz, rw, rx, ry, rz, vx, vy, vz = \
                    struct.unpack(STATE_FORMAT, data)[1:]
            except struct.error:
                print("Bad state packet")
                return
            server_pos = Vector3(px, py, pz)
            server_vel = Vector3(vx, vy, vz)
            if player_id == self.id:
                game_pos = self.parent.position
                game_vel = self.parent.Rigidbody.velocity
                self.position_correction(game_pos, server_pos, game_vel, server_vel)
            else:
                player = self.players.search(player_id)
                if player:
                    player.position = server_pos
                    player.Rigidbody.velocity = server_vel
                else:
                    self.players.add_child(self.game_object(player_id, server_pos, server_vel))
                    print("new player joined")

        elif ptype == PacketType.DAMAGE:
            try:
                hp = struct.unpack(DAMAGE_FORMAT, data)[1]
            except struct.error:
                print("Bad damage packet")
                return
            self.parent.Player.set_hp(hp)

        elif ptype == PacketType.DEATH:
             try:
                player_id = struct.unpack(DEATH_FORMAT, data)[1]
                if player_id == self.id:
                    self.parent.Player.Death()
                else:
                    player = self.players.search(player_id)
                    if player:
                        player.Player.Death()
             except:
                 print("Bad death packet")

        else:
            print("Unknown packet", ptype)

    def receive_input(self):
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

    def send_ping(self):
        now = time.perf_counter()
        self.wait = True

        packet = struct.pack(
            PING_FORMAT,
            PacketType.PING,
            self.id,
            now
        )

        self.udp.sendto(packet, (self.server_ip, 5001))
        self.last_ping_time = now


# =====================
if __name__ == "__main__":
    c = Client("Player1")
    c.login()

    pwd = c.create_room()
    while True:
        c.send_ping()
        time.sleep(2)

