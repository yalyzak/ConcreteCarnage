import mouse
import keyboard
from collections import deque
from bereshit import Quaternion, Vector3

CENTER_X = 960
CENTER_Y = 540

class Controller:
    def __init__(self, speed=5, sensitivity=0.1):
        self.force_amount = speed
        self.force_amount = 10

        self.sensitivity = sensitivity

        self.total_pitch = 0.0
        self.total_yaw = 0.0
        self.sendt = 0

        # queue storing (bool_list, dx, dy)
        self.input_queue = deque(maxlen=100)

        # keys recorded as booleans
        self.keys = [
            'w',
            's',
            'a',
            'd',
            'space',
            'left shift'
        ]

    def keyboard_controller(self, keys, dt):

        if keys[0]:


            forward = self.parent.quaternion.rotate(Vector3(0, 0, 1))
            forward = Vector3(forward.x, 0, forward.z).normalized()

            self.parent.Rigidbody.velocity += forward * self.force_amount * dt

        if keys[1]:
            backward = self.parent.quaternion.rotate(Vector3(0, 0, -1))
            backward = Vector3(backward.x, 0, backward.z).normalized()
            self.parent.Rigidbody.velocity += backward * self.force_amount * dt

        if keys[2]:
            right = self.parent.quaternion.rotate(Vector3(1, 0, 0))
            right = Vector3(right.x, 0, right.z).normalized()
            self.parent.Rigidbody.velocity += right * self.force_amount * dt

        if keys[3]:
            left = self.parent.quaternion.rotate(Vector3(-1, 0, 0))
            left = Vector3(left.x, 0, left.z).normalized()
            self.parent.Rigidbody.velocity += left * self.force_amount * dt

        if keys[4]:
            self.parent.Rigidbody.velocity += Vector3(
                0,
                self.force_amount * 2,
                0
            ) * dt

        if keys[5]:
            self.parent.Rigidbody.velocity -= Vector3(
                0,
                self.force_amount * 2,
                0
            ) * dt

        if keys[6]:
            self.parent.Shoot.onClick()

    def mouse_controller(self, dx, dy):
        sensitivity = 0.001

        # apply rotation
        self.total_yaw -= dx * sensitivity
        self.total_pitch += dy * sensitivity

        self.total_pitch = max(-1.5, min(1.5, self.total_pitch))

        pitch_q = Quaternion.axis_angle(
            Vector3(1, 0, 0),
            self.total_pitch
        )

        yaw_q = Quaternion.axis_angle(
            Vector3(0, 1, 0),
            self.total_yaw
        )

        self.parent.quaternion = yaw_q * pitch_q


class PlayerController(Controller):

    def Start(self):
        mouse.move(CENTER_X, CENTER_Y)

    def Update(self, dt):
        x, y = self.mouse_recorder()
        keys = self.keyboard_recorder()
        self.keyboard_controller(keys, dt)
        self.mouse_controller(x, y)
        self.record_input(keys, x, y)

    def record_input(self, key_states, dx, dy):
        if dx != 0 or dy != 0 or True in key_states:
            # mouse buttons as bools
            bool_list = key_states
            # store input frame
            self.input_queue.append([bool_list, dx, dy])

    def keyboard_recorder(self):
        mouse_left = mouse.is_pressed('left')
        mouse_right = mouse.is_pressed('right')
        key_states = [keyboard.is_pressed(k) for k in self.keys] + [mouse_left, mouse_right]
        return key_states

    @staticmethod
    def mouse_recorder():
        # recenter mouse
        x, y = mouse.get_position()

        dx = x - CENTER_X
        dy = y - CENTER_Y
        mouse.move(CENTER_X, CENTER_Y)

        return dx, dy


class ServerController(Controller):
    def Update(self, dt):
        if self.input_queue:
            keys, dx, dy = self.input_queue.pop()
            keys = [(keys >> i) & 1 == 1 for i in range(32)]
            self.keyboard_controller(keys, dt)
            self.mouse_controller(dx, dy)

    def read_input(self):
        return self.input_queue.pop()
