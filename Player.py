from bereshit import Text


class Player:
    def __init__(self):
        self.HP = 100
        self.HP_Text = Text(str(self.HP), center=(420,850), scale=1)

    def Hit(self, hp):
        self.HP -= hp

    def Start(self):
        self.render = self.parent.World.Camera.Camera.render
        self.render.add_text_rect(self.HP_Text)