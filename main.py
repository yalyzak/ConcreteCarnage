from Client import Client
from bereshit import Object, BoxCollider, Rigidbody, Vector3, Camera, Core, Quaternion
from Movement import PlayerController
from MAP import crateMAP
from protocol import TICK
from debug import debug, debug2
from Shoot import Shoot

# PLAYER
player = Object(
    name="player",
    position=Vector3(5,1,0)
).add_component([
    BoxCollider(),
    Rigidbody(Freeze_Rotation=Vector3(1,1,1), useGravity=True),
    PlayerController(),
    Camera(shading="solid"),
    Client("Player1",), #"192.168.1.163"
    Shoot(),
])

enemy = Object(
    name="enemy",
    position=Vector3(7,10,0)
).add_component([
    BoxCollider(),
    Rigidbody(useGravity=True),


])
camera = Object(name="camera", position=Vector3(0,10,0), rotation=Vector3(90,0,0)).add_component(Camera())


Core.run([player, enemy] + crateMAP(), tick=TICK)