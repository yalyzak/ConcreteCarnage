from bereshit import Text


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
        self.render = self.parent.World.Camera.Camera.render
        self.render.add_text_rect(self._HP_Text)

