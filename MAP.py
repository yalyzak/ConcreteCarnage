from bereshit import Object, BoxCollider, Rigidbody, Vector3, MeshRander
from Movement import PlayerController, ServerController
from ClientHelper import ClientHelper
from Shoot import Shoot
from Player import GamePlayer, ServerPlayer


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
    # ========================
    # MAIN FLOOR
    # ========================

    ground = Object(size=Vector3(40, 1, 40)).add_component([BoxCollider(), Rigidbody(isKinematic=True)])

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
        b.add_component([BoxCollider(), Rigidbody(isKinematic=True)])
        for b in boxes
    ]

    # ========================
    # RAMPS (ELEVATION)
    # ========================

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

    objs = [ground] + walls + mid_walls + boxes + ramps

    return objs


def server_game_object(name, client):
    return Object(name=name, position=Vector3(1, 1, 1)).add_component(
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


def main_game_object():
    from Client import Client
    from UI import UI
    from bereshit import Camera
    return Object(size=Vector3(1, 2, 1), position=Vector3(5, 2, 0)).add_component(
        [
            BoxCollider(),
            Rigidbody(Freeze_Rotation=Vector3(1, 1, 1), useGravity=True),
            Camera(shading="material preview"),
            PlayerController(),
            UI(),
            Client(),  # "192.168.1.163"
            Shoot(True),
            GamePlayer(),
        ])
