import struct
import random

from protocol import PacketType, DAMAGE_FORMAT, SPAWN_FORMAT
from bereshit import Text, Vector3, Quaternion


class Player:
    def __init__(self):
        self._HP = 100
        self._HP_Text = Text(str(self._HP), center=(420,850), scale=1)

    def get_hp(self):
        return self._HP

    def Hit(self, hp):
        self._HP -= hp
        self._HP_Text.text = str(self._HP)

    def Start(self):
        # self.render = self.parent.World.Camera.Camera.render
        # self.render.add_text_rect(self._HP_Text)
        self.Active = False

    def attach(self, _):
        return "Player"

    def respawn(self):
        self.parent.position = Vector3(random.randint(0, 20), 1, random.randint(0, 20))
        self.parent.quaternion *= Quaternion()
        self.parent.size = Vector3(1,1,1)

    def despawn(self):
        self.parent.size = Vector3(0,0,0)
        # self.parent.destroy()

class GamePlayer(Player):
    def set_hp(self, hp):
        self._HP = hp
        self._HP_Text.text = str(int(self._HP))

    def Death(self):
        self.parent.destroy()


class ServerPlayer(Player):
    def damage_message(self):
        return struct.pack(DAMAGE_FORMAT, PacketType.DAMAGE, self._HP)


    def Hit(self, hp):
        self._HP -= hp
        self._HP_Text.text = str(self._HP)
        self.parent.ClientHelper.send(self.damage_message())
        if self._HP <= 0:
            self.parent.ClientHelper.dead()
