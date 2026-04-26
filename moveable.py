import keyboard


class moveable:
    def __init__(self):
        """Initialize moveable object with speed."""
        self.speed = 0.1
    
    def Update(self, dt):
        """Handle movement based on arrow key input."""
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