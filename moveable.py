import keyboard


class moveable:
    def __init__(self):
        self.speed = 0.1
    #     self.render = self.parent.World.Camera.Camera.render
    def Update(self, dt):
        move = self.speed

        # Y axis (up/down)
        if keyboard.is_pressed('up'):
            self.parent.position.z += move
        if keyboard.is_pressed('down'):
            self.parent.position.z -= move

        # X axis (left/right)
        if keyboard.is_pressed('left'):
            self.parent.position.x -= move
        if keyboard.is_pressed('right'):
            self.parent.position.x += move

        # Z axis (forward/backward)
        if keyboard.is_pressed('w'):
            self.parent.position.z += move
        if keyboard.is_pressed('s'):
            self.parent.position.z -= move