import mouse
import keyboard
from collections import deque
from bereshit import Quaternion, Vector3

CENTER_X = 960
CENTER_Y = 540
class Recorder:
    def __init__(self, keys, enable_hooks=True):
        self.keys = keys
        self.state = {k: False for k in keys}
        self.state["mouse_left"] = False
        self.state["mouse_right"] = False
        # self.mouse = self.parent.World.Camera.Camera.render.mouse_input
        if enable_hooks:
            keyboard.hook(self._keyboard_event)
        #     mouse.hook(self._mouse_event)

    def _keyboard_event(self, event):
        if event.name in self.state:
            self.state[event.name] = (event.event_type == "down")

    def _mouse_event(self, event):
        if hasattr(event, "button") and hasattr(event, "event_type"):
            if event.button == "left":
                self.state["mouse_left"] = (event.event_type == "down")
            elif event.button == "right":
                self.state["mouse_right"] = (event.event_type == "down")

    def keyboard_recorder(self):
        return [self.state[k] for k in self.keys] + [
            self.state["mouse_left"],
            self.state["mouse_right"]
        ]

class Controller:
    def __init__(self, speed=5, sensitivity=0.1):
        self.force_amount = speed
        self.force_amount = 10
        self.jump_speed = 50
        self.isGrounded = False
        self.ground_normal = Vector3(0,1,0)
        self.max_velocity = 9.8
        self.sensitivity = sensitivity
        self.max_speed = 5
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
    def attach(self, other):
        self.rb = other.Rigidbody

    def OnCollisionStay(self, collision):
        if self.isGrounded:
            return
        if collision.other.parent.get_component("Ground"):
            self.isGrounded = True
            self.ground_normal = collision.normal

    def OnCollisionEnter(self, collision):
        if self.isGrounded:
            return
        if collision.other.parent.get_component("Ground"):
            self.isGrounded = True
            self.ground_normal = collision.normal

    def OnCollisionExit(self, collision):
        if collision.other.parent.get_component("Ground"):
            self.isGrounded = False


    def keyboard_controller(self, keys, dt):


        if keys[0]:
            forward = self.parent.quaternion.rotate(Vector3(0, 0, 1)).normalized()

            # project onto ground
            n = self.ground_normal
            forward = forward - n * forward.dot(n)
            forward = forward.normalized()
            if n != Vector3(0,1,0):
                print(n)
            horizontal = Vector3(self.rb.velocity.x, 0, self.rb.velocity.z)

            # add acceleration
            horizontal += forward * self.force_amount * dt

            # clamp horizontal speed
            if horizontal.magnitude() > self.max_speed:
                horizontal = horizontal.normalized() * self.max_speed

            # keep vertical velocity untouched
            self.rb.velocity = Vector3(horizontal.x, self.rb.velocity.y, horizontal.z)

            # self.rb.velocity += forward * self.force_amount * dt
        if keys[1]:
            backward = self.parent.quaternion.rotate(Vector3(0, 0, -1))
            # project onto ground
            n = self.ground_normal
            backward = backward - n * backward.dot(n)
            backward = backward.normalized()

            backward = Vector3(backward.x, 0, backward.z).normalized()

            horizontal = Vector3(self.rb.velocity.x, 0, self.rb.velocity.z)

            # add acceleration
            horizontal += backward * self.force_amount * dt

            # clamp horizontal speed
            if horizontal.magnitude() > self.max_speed:
                horizontal = horizontal.normalized() * self.max_speed

            # keep vertical velocity untouched
            self.rb.velocity = Vector3(horizontal.x, self.rb.velocity.y, horizontal.z)

        if keys[2]:
            right = self.parent.quaternion.rotate(Vector3(1, 0, 0))
            right = Vector3(right.x, 0, right.z).normalized()
            horizontal = Vector3(self.rb.velocity.x, 0, self.rb.velocity.z)

            # add acceleration
            horizontal += right * self.force_amount * dt

            # clamp horizontal speed
            if horizontal.magnitude() > self.max_speed:
                horizontal = horizontal.normalized() * self.max_speed

            # keep vertical velocity untouched
            self.rb.velocity = Vector3(horizontal.x, self.rb.velocity.y, horizontal.z)

        if keys[3]:
            left = self.parent.quaternion.rotate(Vector3(-1, 0, 0))
            left = Vector3(left.x, 0, left.z).normalized()
            self.rb.velocity += left * self.force_amount * dt
            horizontal = Vector3(self.rb.velocity.x, 0, self.rb.velocity.z)

            # add acceleration
            horizontal += left * self.force_amount * dt

            # clamp horizontal speed
            if horizontal.magnitude() > self.max_speed:
                horizontal = horizontal.normalized() * self.max_speed

            # keep vertical velocity untouched
            self.rb.velocity = Vector3(horizontal.x, self.rb.velocity.y, horizontal.z)

        if not self.isGrounded:
            keys[4] = False

        if keys[4]:
            self.rb.velocity += Vector3(
                0,
                self.jump_speed * 2,
                0
            ) * dt

        if keys[5]:
            self.rb.velocity -= Vector3(
                0,
                self.jump_speed * 2,
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
        self.Active = False
        self.recorder = Recorder(self.keys)
        self.mouse = self.parent.World.Camera.Camera.render.get_mouse_input

    def Update(self, dt):
        # keys = self.recorder.keyboard_recorder()
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
        mouse_left = self.mouse()
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
