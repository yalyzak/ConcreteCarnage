import os

from bereshit import Core,Camera,Object,Vector3,Rigidbody,BoxCollider, MeshRander
# import Server
# from Client import Client
from Movement import PlayerController
dir = "C:/Users/yaly/Documents/map/"
player = Object(position=Vector3(0,1,0)).add_component([BoxCollider(), Rigidbody(Freeze_Rotation=Vector3(1,1,1)), Camera(shading="solid"), PlayerController()])

floor = Object(size=Vector3(10,1,10)).add_component([BoxCollider(), Rigidbody(isKinematic=True)])

arr = []

# loop through all files in the folder
for file_name in os.listdir(dir):
    full_path = os.path.join(dir, file_name)

    # make sure it's a file (not a subfolder)
    if os.path.isfile(full_path):
        obj = Object().add_component(
            MeshRander(obj_path=full_path)
        )
        arr.append(obj)

Core.run([player,floor] + arr)