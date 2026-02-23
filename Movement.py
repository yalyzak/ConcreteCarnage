import mouse
import keyboard
from collections import deque
from bereshit import Quaternion, Vector3

CENTER_X = 960
CENTER_Y = 540


class PlayerController:
    def __init__(self, speed=5, sensitivity=0.1):
        self.force_amount = speed
        self.sensitivity = sensitivity

        self.total_pitch = 0.0
        self.total_yaw = 0.0

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

    # -----------------------------------
    # START
    # -----------------------------------
    def Start(self):
        mouse.move(CENTER_X, CENTER_Y)

    # -----------------------------------
    # UPDATE
    # -----------------------------------
    def Update(self, dt):
        self.record_input()
        # self.mouse_controller()
        self.keyboard_controller(dt)


    # -----------------------------------
    # INPUT RECORDING
    # -----------------------------------
    def record_input(self):
        x, y = mouse.get_position()

        dx = x - CENTER_X
        dy = y - CENTER_Y

        # keyboard bools
        key_states = [keyboard.is_pressed(k) for k in self.keys]

        # mouse buttons as bools
        mouse_left = mouse.is_pressed('left')
        mouse_right = mouse.is_pressed('right')

        bool_list = key_states + [
            mouse_left,
            mouse_right
        ]

        # store input frame
        self.input_queue.append((bool_list, dx, dy))

    # -----------------------------------
    # MOUSE LOOK
    # -----------------------------------
    def mouse_controller(self):
        x, y = mouse.get_position()

        dx = x - CENTER_X
        dy = y - CENTER_Y

        sensitivity = 0.001

        # apply rotation
        self.total_yaw -= dx * sensitivity
        self.total_pitch += dy * sensitivity

        pitch_q = Quaternion.axis_angle(
            Vector3(1, 0, 0),
            self.total_pitch
        )

        yaw_q = Quaternion.axis_angle(
            Vector3(0, 1, 0),
            self.total_yaw
        )

        self.parent.quaternion = yaw_q * pitch_q

        # recenter mouse
        mouse.move(CENTER_X, CENTER_Y)

    # -----------------------------------
    # KEYBOARD MOVEMENT
    # -----------------------------------
    def keyboard_controller(self, dt):

        if keyboard.is_pressed('w'):
            forward = self.parent.quaternion.rotate(Vector3(0, 0, 1))
            forward = Vector3(forward.x, 0, forward.z).normalized()
            self.parent.Rigidbody.velocity += forward * self.force_amount * dt

        if keyboard.is_pressed('s'):
            backward = self.parent.quaternion.rotate(Vector3(0, 0, -1))
            backward = Vector3(backward.x, 0, backward.z).normalized()
            self.parent.Rigidbody.velocity += backward * self.force_amount * dt

        if keyboard.is_pressed('a'):
            right = self.parent.quaternion.rotate(Vector3(1, 0, 0))
            right = Vector3(right.x, 0, right.z).normalized()
            self.parent.Rigidbody.velocity += right * self.force_amount * dt

        if keyboard.is_pressed('d'):
            left = self.parent.quaternion.rotate(Vector3(-1, 0, 0))
            left = Vector3(left.x, 0, left.z).normalized()
            self.parent.Rigidbody.velocity += left * self.force_amount * dt

        if keyboard.is_pressed('space'):
            self.parent.Rigidbody.velocity += Vector3(
                0,
                self.force_amount * 3,
                0
            ) * dt

        if keyboard.is_pressed('left shift'):
            self.parent.Rigidbody.velocity += Vector3(
                0,
                -self.force_amount * 3,
                0
            ) * dt