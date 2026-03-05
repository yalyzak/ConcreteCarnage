# client.py
import random
import socket
import struct
import time
import select

from bereshit import Vector3

from protocol import PacketType, CLIENT_PACK_FORMAT, PING_FORMAT, PONG_FORMAT, STATE_FORMAT

class Client:

    def __init__(self, name, ip = "127.0.0.1"):
        self.name = name
        self.id = None

        self.server_ip = ip

        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.udp.setblocking(False)
        self.udp.settimeout(0.0002)  # seconds

        self.last_ping_time = 0
        self.wait = False
    def attach(self, owner_object):
        self.input = owner_object.PlayerController.input_queue.popleft

    def Update(self, dt):
        bools, dx, dy = self.input()
        self.send_input(bools, dx, dy, dt)
        if time.perf_counter() - self.last_ping_time > 0.1:
            if not self.wait:
                self.send_ping()

        self.receive_input()
    def Start(self):
        self.login()
        self.create_room("room1"+ str(random.randint(1, 100 )))
    def login(self):
        try:
            self.tcp.connect((self.server_ip, 5000))
            self.tcp.send(self.name.encode())

            msg = self.tcp.recv(128).decode()
            self.id = int(msg.split()[1])
        except Exception as e:
            print("Login failed", e)
            raise

    def create_room(self, room):
        self.tcp.send(f"CREATE {room}".encode())
        print(self.tcp.recv(128).decode())

    def join_room(self, room, pwd):
        self.tcp.send(f"JOIN {room} {pwd}".encode())
        print(self.tcp.recv(128).decode())

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
    def position_correction(self, game_pos, server_pos, game_vel, server_vel):


        # --- Settings ---
        snap_distance = 0.08  # if too far away -> teleport
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
            print(f"Ping: {ping:.2f} ms")

        elif ptype == PacketType.STATE:
            try:
                px, py, pz, rw, rx, ry, rz, vx, vy, vz = \
                    struct.unpack(STATE_FORMAT, data)[1:]
            except struct.error:
                print("Bad state packet")
                return

            game_pos = self.parent.position
            server_pos = Vector3(px, py, pz)
            game_vel = self.parent.Rigidbody.velocity
            server_vel = Vector3(vx, vy, vz)

            self.position_correction(game_pos, server_pos, game_vel, server_vel)

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

    c.create_room("room1")

