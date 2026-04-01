from bereshit import Object, BoxCollider, Rigidbody, Vector3, MeshRander
from Movement import PlayerController, ServerController
from ClientHelper import ClientHelper
from Shoot import Shoot
from Player import GamePlayer, ServerPlayer

def build_block(position=Vector3(0,0,0), size=Vector3(1,1,1), rotation=Vector3(0,0,0)):
    return Object(position=position, size=size, rotation=rotation).add_component([BoxCollider(), Rigidbody(isKinematic=True)])


def client_map():
    # ========================
    # MAIN FLOOR
    # ========================

    tile_size = 40 / 3
    spacing = tile_size * 0.95  # smaller spacing = overlap

    ground = []

    rotations = [
        0, 90, 180,
        270, 0, 90,
        180, 270, 0
    ]

    i = 0
    for x in range(3):
        for z in range(3):
            tile = Object(
                position=Vector3((x - 1) * spacing, 0, (z - 1) * spacing),
                rotation=Vector3(0, rotations[i], 0),
                size=Vector3(tile_size, 1, tile_size)
            ).add_component([
                BoxCollider(),
                Rigidbody(isKinematic=True),
                MeshRander(obj_path="models/destroyed_concrete_slab_with_reinforcement.glb")
            ])

            ground.append(tile)
            i += 1

    # ========================
    # OUTER WALLS (MAP BORDER)
    # ========================

    walls = [
        Object(position=Vector3(0, 5, 20), size=Vector3(40, 10, 1)),
        Object(position=Vector3(0, 5, -20), size=Vector3(40, 10, 1)),
        Object(position=Vector3(20, 5, 0), size=Vector3(1, 10, 40)),
        Object(position=Vector3(-20, 5, 0), size=Vector3(1, 10, 40))
    ]

    walls = [
        w.add_component([BoxCollider(), Rigidbody(isKinematic=True)])
        for w in walls
    ]

    # ========================
    # MID LANE WALLS
    # ========================

    mid_walls = [
        Object(position=Vector3(0, 2, 0), size=Vector3(2, 4, 12)),
        Object(position=Vector3(-6, 2, 5), size=Vector3(6, 4, 2)),
        Object(position=Vector3(6, 2, -5), size=Vector3(6, 4, 2)),
    ]

    mid_walls = [
        w.add_component([BoxCollider(), Rigidbody(isKinematic=True)])
        for w in mid_walls
    ]

    # ========================
    # COVER BOXES (CS STYLE)
    # ========================
    boxes = [
        Object(position=Vector3(-10, 1, 10), size=Vector3(2, 2, 4)),
        Object(position=Vector3(-12, 1, 8), size=Vector3(2, 2, 4), rotation=Vector3(0, 90, 0)),
        Object(position=Vector3(10, 1, -10), size=Vector3(2, 2, 2)),
        Object(position=Vector3(12, 1, -8), size=Vector3(2, 2, 2)),
        Object(position=Vector3(0, 1, 15), size=Vector3(3, 2, 3)),
        Object(position=Vector3(0, 1, -15), size=Vector3(3, 2, 3)),
    ]

    boxes = [
        b.add_component(
            [BoxCollider(), Rigidbody(isKinematic=True), MeshRander(obj_path="models/concrete_block_low_poly.glb")])
        for b in boxes
    ]

    # ========================
    # RAMPS (ELEVATION)
    # ========================
    # ramp = MeshRander(obj_path="models/ramp.glb")

    ramps = [
        Object(
            position=Vector3(-15, 0.5, 0),
            size=Vector3(10, 1, 10),
            rotation=Vector3(15, 0, 0)
        ),
        Object(
            position=Vector3(15, 0.5, 0),
            size=Vector3(10, 1, 10),
            rotation=Vector3(-15, 0, 0)
        )
    ]

    ramps = [
        r.add_component([BoxCollider(), Rigidbody(isKinematic=True)])
        for r in ramps
    ]

    # ========================
    # BOMB SITE AREAS (OPEN SPACES)
    # ========================

    siteA = Object(
        position=Vector3(-15, 0, 15),
        size=Vector3(10, 1, 10)
    ).add_component([BoxCollider(), Rigidbody(isKinematic=True)])

    siteB = Object(
        position=Vector3(15, 0, -15),
        size=Vector3(10, 1, 10)
    ).add_component([BoxCollider(), Rigidbody(isKinematic=True)])

    objs = ground + walls + mid_walls + boxes + ramps

    return objs


def server_map():
    floor_height = 5
    ground_height = floor_height * 0.5
    ground = build_block(size=Vector3(50,1,50), position=Vector3(0,-0.5,0))

    building_NW = [build_block(size=Vector3(20,floor_height,1), position=Vector3(15,ground_height,25.5)),
                   build_block(size=Vector3(1,floor_height,19), position=Vector3(24.5,ground_height,15.5)),
                   build_block(size=Vector3(4, floor_height, 1), position=Vector3(14, ground_height, 6.5)),
                   build_block(size=Vector3(5, floor_height, 1), position=Vector3(21.5, ground_height, 6.5)),
                   build_block(size=Vector3(1, floor_height, 8), position=Vector3(11.5, ground_height, 10)),
                   build_block(size=Vector3(7,floor_height,1), position=Vector3(8.5,ground_height,14.5)),
                   build_block(size=Vector3(1, floor_height, 3), position=Vector3(5.5, ground_height, 16.5)),
                   build_block(size=Vector3(1, floor_height, 4), position=Vector3(5.5, ground_height, 23)),
                   ]

    building_SW = [
                    build_block(size=Vector3(1, floor_height, 19), position=Vector3(24.5, ground_height, -15.5)),
                    build_block(size=Vector3(20, floor_height, 1), position=Vector3(15, ground_height, -25.5)),
                    build_block(size=Vector3(1, floor_height, 6), position=Vector3(5.5, ground_height, -22)),
                    build_block(size=Vector3(1, floor_height, 5), position=Vector3(5.5, ground_height, -14)),
                    build_block(size=Vector3(8, floor_height, 1), position=Vector3(10, ground_height, -12)),
                    build_block(size=Vector3(1, floor_height, 1), position=Vector3(13.5, ground_height, -11)),
                    build_block(size=Vector3(1, floor_height, 2), position=Vector3(13.5, ground_height, -7)),
                    build_block(size=Vector3(10, floor_height, 1), position=Vector3(19, ground_height, -6.5)),

                   ]


    return [ground] + building_NW + building_SW


def server_game_object(name, client):
    return Object(name=name, size=Vector3(1, 2, 1)).add_component(
        [
            BoxCollider(),
            Rigidbody(Freeze_Rotation=Vector3(1, 1, 1), useGravity=True, velocity=Vector3(0, 0, 0)),
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
    cam = Object(position=Vector3(0,1.8,0)).add_component(Camera(shading="material preview"))
    player = Object(size=Vector3(1, 1.8, 1), children=[cam]).add_component(
        [
            BoxCollider(),
            Rigidbody(Freeze_Rotation=Vector3(1, 1, 1), useGravity=True),
            # Camera(shading="material preview"),
            PlayerController(),
            Client(ip=ip),  # "192.168.1.163"
            Shoot(True),
            UI(),
            GamePlayer(),
            MeshRander(shape="empty")
        ])
    return player
