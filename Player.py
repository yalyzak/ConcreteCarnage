import struct
import random

from protocol import PacketType, DAMAGE_FORMAT
from bereshit import Text, Vector3, Quaternion


class Player:
    def __init__(self):
        """Initialize player with default health values."""
        self._HP = 100
        self._MaxHp = 100

    def get_hp(self):
        """Return current player health points."""
        return self._HP

    def Hit(self, hp):
        """Reduce health by given damage amount."""
        self._HP -= hp




    def Start(self):
        """Initialize player component (called on startup)."""
        # self.render = self.parent.World.Camera.Camera.render
        # self.render.add_text_rect(self._HP_Text)
        self.Active = False

    def attach(self, _):
        """Attach player to parent object."""
        return "Player"

    def respawn(self):
        """Reset player position and health to initial state."""
        self.parent.position = Vector3(random.randint(0, 20), 1, random.randint(0, 20))
        self.parent.quaternion *= Quaternion()
        self.parent.size = Vector3(1,1,1)
        self._HP = self._MaxHp

    def despawn(self):
        """Hide player by setting size to zero."""
        self.parent.size = Vector3(0,0,0)
        # self.parent.destroy()


class GamePlayer(Player):
    def attach(self, parent):
        """Attach to UI component for HUD updates."""
        self.UI = parent.get_component("GameUI")
        return "Player"

    def Hit(self, hp):
        """Update health and UI when player takes damage."""
        self._HP = hp
        if self.UI:
            self.parent.GameUI.update_hp(self._HP, self._MaxHp)
        if self._HP <= 0:
            if self.UI:
                self.parent.GameUI.esc()

    def Death(self):
        """Handle player death event."""
        pass
        # self.parent.GameUI.Death()
        # self.parent.destroy()


class ServerPlayer(Player):
    def Hit(self, hp):
        """Reduce health and notify client of damage taken."""
        self._HP -= hp
        self.parent.ClientHelper.send_udp((self._HP, PacketType.DAMAGE))
        if self._HP <= 0:
            self.despawn() # need better securty so player wouldnt be abele to keep playing

        #     self.parent.ClientHelper.dead()

