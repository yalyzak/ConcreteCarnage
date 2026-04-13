from moveable import moveable
from bereshit import Object, BoxCollider, Rigidbody, Vector3, MeshRander, Quaternion
from Movement import PlayerController, ServerController
from ClientHelper import ClientHelper
from Shoot import Shoot
from Player import GamePlayer, ServerPlayer
from Ground import Ground


def build_block(position=Vector3(0, 0, 0), size=Vector3(1, 1, 1), rotation=Vector3(0, 0, 0), texture=False):
    if texture:
        return Object(position=position, size=size, rotation=rotation).add_component(
            [BoxCollider(), Rigidbody(isKinematic=True), Ground(),
             MeshRander(shape="box", texture="models/concrete_texture.jpg", repeat_texture=True)])

    return Object(position=position, size=size, rotation=rotation).add_component(
        [BoxCollider(), Rigidbody(isKinematic=True), Ground()])


def build_ramp(starting_point, end_point, texture=False):
    direction = end_point - starting_point
    length = direction.magnitude()

    rot_q = Quaternion.look_rotation(direction.normalized(), Vector3(0,1,0))
    rotation = -rot_q.to_euler()

    # Center position (middle of ramp)
    position = starting_point + direction * 0.5

    size = Vector3(2, 1, length)  # width, height, length

    # 👇 compute ramp's local UP direction
    up = rot_q.rotate(Vector3(0, 1, 0))  # or conjugate().rotate if your system needs it

    # 👇 shift DOWN by half height so top face aligns with line
    position -= up * (size.y * 0.5)

    return build_block(position=position, size=size, rotation=rotation)



def build_wall(position=Vector3(0, 0, 0), size=Vector3(1, 1, 1), rotation=Vector3(0, 0, 0), texture=False):
    if texture:
        return Object(position=position, size=size, rotation=rotation).add_component(
            [BoxCollider(), Rigidbody(isKinematic=True),
             MeshRander(shape="box", texture="models/wall_texture.jpg", repeat_texture=True)])

    return Object(position=position, size=size, rotation=rotation).add_component(
        [BoxCollider(), Rigidbody(isKinematic=True)])


def server_map():
    floor_height = 6
    floor2_height = 7
    floor_height2 = 2

    ground_height = floor_height * 0.5
    ground = build_block(size=Vector3(50, 1, 50), position=Vector3(0, -0.5, 0))

    # ── NW BUILDING ──────────────────────────────────────────────
    building_NW_f1 = [
        build_wall(size=Vector3(20, floor_height, 1), position=Vector3(15, ground_height, 25.5)),
        build_wall(size=Vector3(1, floor_height, 19), position=Vector3(24.5, ground_height, 15.5)),
        build_wall(size=Vector3(4, floor_height, 1), position=Vector3(14, ground_height, 6.5)),
        build_wall(size=Vector3(5, floor_height, 1), position=Vector3(21.5, ground_height, 6.5)),
        build_wall(size=Vector3(1, floor_height, 8), position=Vector3(11.5, ground_height, 10)),
        build_wall(size=Vector3(7, floor_height, 1), position=Vector3(8.5, ground_height, 14.5)),
        build_wall(size=Vector3(1, floor_height, 3), position=Vector3(5.5, ground_height, 16.5)),
        build_wall(size=Vector3(1, floor_height, 4), position=Vector3(5.5, ground_height, 23)),

    ]
    building_NW_f2 = [
        build_block(size=Vector3(7, 1, 4), position=Vector3(18, 0.4, 23), rotation=Vector3(0, 0, -15)),
        build_block(size=Vector3(5, 1, 4), position=Vector3(23.74, 1.286, 23)),
        build_block(size=Vector3(3, 1, 12.75), position=Vector3(22.6, 3.35, 15.86), rotation=Vector3(-20, 0, 0)),
        build_block(size=Vector3(5, 1, 3.2), position=Vector3(21.5, floor_height - 0.5, 8.45)),
        build_block(size=Vector3(13, 1, 10), position=Vector3(12.5, floor_height - 0.5, 20)),
        build_block(size=Vector3(7, 1, 8), position=Vector3(15.5, floor_height - 0.5, 11)),

        build_wall(size=Vector3(20, floor_height2, 1), position=Vector3(15, floor2_height, 25.5)),
        build_wall(size=Vector3(1, floor_height2, 19), position=Vector3(24.5, floor2_height, 15.5)),
        build_wall(size=Vector3(13, floor_height2, 1), position=Vector3(17.5, floor2_height, 6.5)),
        build_wall(size=Vector3(1, floor_height2, 19), position=Vector3(10.5, floor2_height, 15.5)),
        build_block(size=Vector3(3, 0.5, 7), position=Vector3(12.5, 6.8, 10.4), rotation=Vector3(-17, 0, 0)),

    ]

    # ── SW BUILDING ──────────────────────────────────────────────
    building_SW = [
        build_wall(size=Vector3(1, floor_height, 19), position=Vector3(24.5, ground_height, -15.5)),
        build_wall(size=Vector3(20, floor_height, 1), position=Vector3(15, ground_height, -25.5)),
        build_wall(size=Vector3(1, floor_height, 6), position=Vector3(5.5, ground_height, -22)),
        build_wall(size=Vector3(1, floor_height, 5), position=Vector3(5.5, ground_height, -14)),
        build_wall(size=Vector3(8, floor_height, 1), position=Vector3(10, ground_height, -12)),
        build_wall(size=Vector3(1, floor_height, 1), position=Vector3(13.5, ground_height, -11)),
        build_wall(size=Vector3(1, floor_height, 2), position=Vector3(13.5, ground_height, -7)),
        build_wall(size=Vector3(10, floor_height, 1), position=Vector3(19, ground_height, -6.5)),
    ]

    # ── NE BUILDING ──────────────────────────────────────────────
    # Mirror of NW across X axis (negate all X positions, flip wall orientations)
    building_NE = [
        build_wall(size=Vector3(20, floor_height, 1), position=Vector3(-15, ground_height, 25.5)),
        build_wall(size=Vector3(1, floor_height, 19), position=Vector3(-24.5, ground_height, 15.5)),
        build_wall(size=Vector3(4, floor_height, 1), position=Vector3(-14, ground_height, 6.5)),
        build_wall(size=Vector3(5, floor_height, 1), position=Vector3(-21.5, ground_height, 6.5)),
        build_wall(size=Vector3(1, floor_height, 8), position=Vector3(-11.5, ground_height, 10)),
        build_wall(size=Vector3(7, floor_height, 1), position=Vector3(-8.5, ground_height, 14.5)),
        build_wall(size=Vector3(1, floor_height, 3), position=Vector3(-5.5, ground_height, 16.5)),
        build_wall(size=Vector3(1, floor_height, 4), position=Vector3(-5.5, ground_height, 23)),
    ]

    # ── SE BUILDING ──────────────────────────────────────────────
    # Mirror of SW across X axis
    building_SE = [
        build_wall(size=Vector3(1, floor_height, 19), position=Vector3(-24.5, ground_height, -15.5)),
        build_wall(size=Vector3(20, floor_height, 1), position=Vector3(-15, ground_height, -25.5)),
        build_wall(size=Vector3(1, floor_height, 6), position=Vector3(-5.5, ground_height, -22)),
        build_wall(size=Vector3(1, floor_height, 5), position=Vector3(-5.5, ground_height, -14)),
        build_wall(size=Vector3(8, floor_height, 1), position=Vector3(-10, ground_height, -12)),
        build_wall(size=Vector3(1, floor_height, 1), position=Vector3(-13.5, ground_height, -11)),
        build_wall(size=Vector3(1, floor_height, 2), position=Vector3(-13.5, ground_height, -7)),
        build_wall(size=Vector3(10, floor_height, 1), position=Vector3(-19, ground_height, -6.5)),
    ]

    # ── CENTRAL MID BLOCKER ───────────────────────────────────────
    # Small building in the centre forcing players to go around,
    # two entrances (N and S gaps), sitting between the four quadrants
    building_mid = [
        # North wall — two segments with a door gap in the middle
        build_wall(size=Vector3(3, floor_height, 1), position=Vector3(-3.5, ground_height, 4.5)),
        build_wall(size=Vector3(3, floor_height, 1), position=Vector3(3.5, ground_height, 4.5)),
        # South wall — two segments with a door gap in the middle
        build_wall(size=Vector3(3, floor_height, 1), position=Vector3(-3.5, ground_height, -4.5)),
        build_wall(size=Vector3(3, floor_height, 1), position=Vector3(3.5, ground_height, -4.5)),
        # West wall — solid
        build_wall(size=Vector3(1, floor_height, 10), position=Vector3(-4.5, ground_height, 0)),
        # East wall — solid
        build_wall(size=Vector3(1, floor_height, 10), position=Vector3(4.5, ground_height, 0)),

        build_wall(size=Vector3(2, 1, 2), position=Vector3(-3, 0, -3)),

        build_wall(size=Vector3(2, 1, 2), position=Vector3(-3, (floor_height - 0.5) / 2, 3)),

        # build_wall(size=Vector3(2, 1, 2), position=Vector3(3, (floor_height - 0.5), 3)),

        build_ramp(starting_point=Vector3(-3, 0.5, -2), end_point=Vector3(-3, (floor_height+0.5) / 2, 2)),

    ]

    # ── NE INNER BLOCK ────────────────────────────────────────────
    # Sits in the north-east alley corridor, breaks sightlines
    building_ne_inner = [
        # North wall — solid
        build_block(size=Vector3(8, floor_height, 1), position=Vector3(-9, ground_height, -6.5)),
        # South wall — split with west-side entrance
        build_block(size=Vector3(3, floor_height, 1), position=Vector3(-13.5, ground_height, -2.5)),
        build_block(size=Vector3(3, floor_height, 1), position=Vector3(-8.5, ground_height, -2.5)),
        # West wall — split with south-side entrance
        build_block(size=Vector3(1, floor_height, 2), position=Vector3(-13.5, ground_height, -8)),
        build_block(size=Vector3(1, floor_height, 1), position=Vector3(-13.5, ground_height, -4)),
        # East wall — solid
        build_block(size=Vector3(1, floor_height, 5), position=Vector3(-5.5, ground_height, -5)),
    ]

    # ── SW INNER BLOCK ────────────────────────────────────────────
    # Sits in the south-west alley corridor, mirrors NE inner
    building_sw_inner = [
        # South wall — solid
        build_block(size=Vector3(8, floor_height, 1), position=Vector3(9, ground_height, 6.5)),
        # North wall — split with east-side entrance
        build_block(size=Vector3(3, floor_height, 1), position=Vector3(13.5, ground_height, 2.5)),
        build_block(size=Vector3(3, floor_height, 1), position=Vector3(8.5, ground_height, 2.5)),
        # East wall — split with north-side entrance
        build_block(size=Vector3(1, floor_height, 2), position=Vector3(13.5, ground_height, 8)),
        build_block(size=Vector3(1, floor_height, 1), position=Vector3(13.5, ground_height, 4)),
        # West wall — solid
        build_block(size=Vector3(1, floor_height, 5), position=Vector3(5.5, ground_height, 5)),
    ]

    # ── MARKET SQUARE COVER ───────────────────────────────────────
    # Low stalls and a pillar in the open centre area
    market_cover = [
        # Stall counters (crouch height — 1.2 tall)
        build_block(size=Vector3(3, 1.2, 1), position=Vector3(-1, 0.6, -1)),
        build_block(size=Vector3(1, 1.2, 3), position=Vector3(2, 0.6, 1)),
        build_block(size=Vector3(3, 1.2, 1), position=Vector3(0, 0.6, 3)),
        # Tall pillar — full body cover
        build_block(size=Vector3(1, 2.5, 1), position=Vector3(0, 1.25, 0)),
    ]

    # ── ALLEY CLUTTER ─────────────────────────────────────────────
    # Small debris blocks scattered through corridors for micro-cover
    alley_clutter = [
        build_block(size=Vector3(1, 1, 2), position=Vector3(3, 0.5, 13)),
        build_block(size=Vector3(2, 1, 1), position=Vector3(-3, 0.5, 11)),
        build_block(size=Vector3(1, 1, 1), position=Vector3(18, 0.5, 3)),
        build_block(size=Vector3(2, 1, 1), position=Vector3(18, 0.5, -3)),
        build_block(size=Vector3(1, 1, 2), position=Vector3(-3, 0.5, -11)),
        build_block(size=Vector3(2, 1, 1), position=Vector3(3, 0.5, -13)),
        build_block(size=Vector3(1, 1, 1), position=Vector3(-18, 0.5, 3)),
        build_block(size=Vector3(1, 1, 2), position=Vector3(-18, 0.5, -4)),
    ]

    return (
            [ground]
            # + building_NW_f1
            # + building_NW_f2
            # + building_SW
            # + building_NE
            # + building_SE
            + building_mid
        # + building_ne_inner
        # + building_sw_inner
        # + market_cover
        # + alley_clutter
    )


def server_game_object(name, client):
    return Object(name=name, size=Vector3(1, 1, 1)).add_component(
        [
            BoxCollider(),
            Rigidbody(Freeze_Rotation=Vector3(1, 1, 1), useGravity=True, velocity=Vector3(0, 0, 0), restitution=0.1),
            ServerController(),
            ClientHelper(client),
            Shoot(False),
            ServerPlayer()
        ])


def client_game_object(player_id, server_pos, server_vel):
    return Object(name=player_id, position=server_pos).add_component(
        [
            BoxCollider(),
            Rigidbody(Freeze_Rotation=Vector3(1, 1, 1), velocity=server_vel),
            GamePlayer()
        ])


def main_game_object(ip="127.0.0.1"):
    from Client import Client
    from UI import UI
    from bereshit import Camera
    from bereshit.addons.essentials import PlayerController as pas
    cam = Object(position=Vector3(0, 1.8, 0)).add_component(Camera(shading="material preview"))
    player = Object(size=Vector3(1, 1, 1), children=[cam], name="player").add_component(
        [
            BoxCollider(),
            Rigidbody(Freeze_Rotation=Vector3(1, 1, 1), useGravity=True, restitution=0.1),
            # Camera(shading="material preview"),
            PlayerController(),
            # pas(),
            Client(ip=ip),  # "192.168.1.163"
            Shoot(True),
            UI(),
            GamePlayer(),
            MeshRander(shape="empty")
        ])
    return player
