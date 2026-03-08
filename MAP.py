from bereshit import Object, BoxCollider, Rigidbody, Vector3, Camera, Core, MeshRander


def crateMAP():

    # ========================
    # MAIN FLOOR
    # ========================

    ground = Object(
        size=Vector3(40,1,40)
    ).add_component([
        BoxCollider(),
        Rigidbody(isKinematic=True)
    ])

    # ========================
    # OUTER WALLS (MAP BORDER)
    # ========================

    walls = [
        Object(position=Vector3(0,5,20), size=Vector3(40,10,1)),
        Object(position=Vector3(0,5,-20), size=Vector3(40,10,1)),
        Object(position=Vector3(20,5,0), size=Vector3(1,10,40)),
        Object(position=Vector3(-20,5,0), size=Vector3(1,10,40))
    ]

    walls = [
        w.add_component([BoxCollider(), Rigidbody(isKinematic=True)])
        for w in walls
    ]

    # ========================
    # MID LANE WALLS
    # ========================

    mid_walls = [
        Object(position=Vector3(0,2,0), size=Vector3(2,4,12)),
        Object(position=Vector3(-6,2,5), size=Vector3(6,4,2)),
        Object(position=Vector3(6,2,-5), size=Vector3(6,4,2)),
    ]

    mid_walls = [
        w.add_component([BoxCollider(), Rigidbody(isKinematic=True)])
        for w in mid_walls
    ]

    # ========================
    # COVER BOXES (CS STYLE)
    # ========================

    boxes = [
        Object(position=Vector3(-10,1,10), size=Vector3(2,2,2)).add_component(MeshRander(obj_path="models/concrete_block_low_poly.glb")),
        Object(position=Vector3(-12,1,8), size=Vector3(2,2,2)),
        Object(position=Vector3(10,1,-10), size=Vector3(2,2,2)),
        Object(position=Vector3(12,1,-8), size=Vector3(2,2,2)),
        Object(position=Vector3(0,1,15), size=Vector3(3,2,3)),
        Object(position=Vector3(0,1,-15), size=Vector3(3,2,3)),
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
            position=Vector3(-15,0.5,0),
            size=Vector3(6,1,10),
            rotation=Vector3(15,0,0)
        ),
        Object(
            position=Vector3(15,0.5,0),
            size=Vector3(6,1,10),
            rotation=Vector3(-15,0,0)
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
        position=Vector3(-15,0,15),
        size=Vector3(10,1,10)
    ).add_component([BoxCollider(), Rigidbody(isKinematic=True)])

    siteB = Object(
        position=Vector3(15,0,-15),
        size=Vector3(10,1,10)
    ).add_component([BoxCollider(), Rigidbody(isKinematic=True)])

    objs = [ground, siteA, siteB] + walls + mid_walls + boxes + ramps

    return objs
