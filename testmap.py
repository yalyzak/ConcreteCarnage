from bereshit import Core, Object, Camera, Rigidbody, BoxCollider, Vector3
from bereshit.addons.essentials import CamController, FPS_cam, PlayerController
from MAP import server_map, main_game_object
from protocol import TICK

player = Object(position=Vector3(0,30,0), rotation=Vector3(90,0,0)).add_component([Camera(shading="material preview"), Rigidbody(isKinematic=True), BoxCollider(is_trigger=True), FPS_cam(), CamController()])
# player = Object(position=Vector3(0,30,0), rotation=Vector3(90,0,0), size=Vector3(1,3,4)).add_component([Camera(shading="material preview"), Rigidbody(Freeze_Rotation=Vector3(1,1,1)), BoxCollider(), FPS_cam(), PlayerController()])

Core.run([player] + server_map(), tick=TICK)
