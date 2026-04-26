from bereshit import Object, Camera, Core, Vector3, MeshRander, Rigidbody, BoxCollider
from UI import HomeUI, PlayUI, GameUI, PlayWithFriends
from MAP import crateMAPServer
from Client import Client
from Movement import PlayerController
from Shoot import Shoot
# player = Object(
#     name="player",
#     position=Vector3(0,0,-10)
# ).add_component([
#     MeshRander(obj_path="models/Player.glb")
# ])


cam = Object(position=Vector3(0,10,0)).add_component([Camera(), HomeUI(), PlayUI(), GameUI(), PlayWithFriends(), PlayerController(), Client(), Rigidbody(Freeze_Rotation=Vector3(1,1,1)), BoxCollider(), Shoot()])

Core.run([cam] + crateMAPServer())