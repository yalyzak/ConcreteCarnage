from bereshit import Core, Object, Camera, Rigidbody, BoxCollider, Vector3
from bereshit.addons.essentials import CamController, FPS_cam
from MAP import server_map, client_map
from protocol import TICK

player = Object(position=Vector3(0,30,0), rotation=Vector3(90,0,0)).add_component([Camera(shading="material preview"), Rigidbody(isKinematic=True), BoxCollider(is_trigger=True), FPS_cam(), CamController()])

Core.run([player] + client_map(), tick=TICK)
