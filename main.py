from Client import Client
# import Server
# PLAYER
from bereshit import Object, BoxCollider, Rigidbody, Vector3, Camera, Core, Quaternion
from Movement import PlayerController
from MAP import crateMAP
from debug import debug

# PLAYER
player = Object(
    name="player",
    position=Vector3(5,1,0)
).add_component([
    BoxCollider(),
    Rigidbody(Freeze_Rotation=Vector3(1,1,1), useGravity=True),
    PlayerController(),
    Camera(shading="solid"),
    Client("Player1", "10.100.102.18"),

])
camera = Object(name="camera", position=Vector3(0,10,0), rotation=Vector3(90,0,0)).add_component(Camera())
box = Object(name="box", size=Vector3(10, 1, 5), rotation=Vector3(0, 0, 0)).add_component(
            [BoxCollider(), Rigidbody(isKinematic=True)])

Core.run([player, box] + crateMAP())