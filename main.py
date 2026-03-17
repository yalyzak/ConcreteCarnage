from Client import Client
from bereshit import Object, BoxCollider, Rigidbody, Vector3, Camera, Core, Quaternion
from Movement import PlayerController
from MAP import crateMAPServer as crateMAP
from protocol import TICK
from debug import debug, debug2
from Shoot import Shoot
from Player import GamePlayer
from UI import HomeUI, PlayWithFriends, PlayUI, GameUI
# PLAYER
player = Object(
    name="player",
    position=Vector3(5,1,0)
).add_component([
    BoxCollider(),
    Rigidbody(Freeze_Rotation=Vector3(1,1,1), useGravity=True),
    Camera(shading="material preview"),
    HomeUI(),
    PlayWithFriends(),
    PlayUI(),
    GameUI(),
    PlayerController(),
    Client(), #"192.168.1.163"
    Shoot(True),
    GamePlayer(),
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