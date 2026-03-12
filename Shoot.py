import random

from bereshit import Object,Camera,Vector3, Rigidbody, BoxCollider, MeshRander, Quaternion, Render, Physics
import mouse  # pip install mouse
from bereshit.render import Text,Box

import copy
class Shoot:
    def __init__(self):
        self.CoolDown = 0.5   # seconds between shots
        self.timer = 0.0      # time passed since last shot
        self.speed = 10
        self.force = 20
        self.shots = 10
        self.MaxShoots = 10
        self.shots_text = Text(str(self.shots), center=(120,850), scale=1)
        self.gimos = Object(position=Vector3(1000,1000,1000),size=Vector3(.1,.1,.1))
        self.Damage = 50

    def onClick(self):
        if self.shots <= 0:
            self.shots = self.MaxShoots
            self.timer = 0
            return
        elif self.timer >= self.CoolDown:
            self.shots -= 1
            self.timer = 0

            self.shots_text.text = str(self.shots)

            forward = self.parent.quaternion.rotate(Vector3(0, 0, 1))
            hits = Physics.RaycastAll(self.parent.position.to_np(), forward.to_np(), self.parent.World)
            for hit in hits:
                if hit.point is not None and hit.collider != self.parent.Collider:
                    Player = hit.collider.parent.get_component("Player")
                    if Player:
                        Player.Hit(self.Damage)
                        # hit.collider.parent.Rigidbody.AddForce(forward * self.force)
    def Start(self):
        self.render = self.parent.World.Camera.Camera.render
        # self.render.add_text_rect(self.shots_text)
        self.Active = False

    def Update(self, dt):
        self.timer += dt

