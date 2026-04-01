from bereshit import Core, Object, Camera, Rigidbody, BoxCollider, Vector3
from bereshit.addons.essentials import CamController, FPS_cam
from MAP import server_map, main_game_object
from protocol import TICK

player = Object(position=Vector3(0,30,0), rotation=Vector3(90,0,0)).add_component([Camera(), Rigidbody(isKinematic=True), BoxCollider(is_trigger=True), FPS_cam(), CamController()])

Core.run([player] + server_map(), tick=TICK)
