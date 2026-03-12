import random
import string
import time

import keyboard
import mouse
from ContentFilter import ContentFilter
keyboard.hook(lambda e: None)

from bereshit.render import Text, Box

titles = [
    "No Mercy. No Escape.",
    "Where Steel Meets Blood.",
    "Only the Dead Leave the Arena.",
    "Fight Until Nothing Moves.",
    "Survive the Streets.",
    "Built on Concrete. Fueled by Carnage.",
    "The City Is Your Battlefield.",
    "War in Every Block.",
    "Concrete Streets. Relentless Combat.",
    "The War Beneath the Skyline.",
    "Lock. Load. Survive.",
    "Enter the Killing Grounds.",
    "Frag Everything.",
    "One Map. Endless Carnage.",
    "Shoot First. Respawn Later."
]
chat_filter = ContentFilter()

class UI:
    def __init__(self):
        self.show = False
        self.buttons = []

    def Start(self):
        self.render = self.parent.World.Camera.Camera.render
        self.Active = False
        self.client = self.parent.Client

    def setup_layout(self):
        pass

    def Update(self, dt):
        if not self.show:
            self.setup_layout()

        if mouse.is_pressed('left'):
             for button in self.buttons:
                if button.click(mouse.get_position()):
                    self.ButtonClicked(button)

    def get_pressed_keys(self, text):
        start = time.perf_counter()
        text.text = ""
        self.render.text_input = -1
        while True:
            time.sleep(0.01)
            """
            Returns a list of pressed keys as readable text.
            Non-blocking.
            """
            if mouse.is_pressed('left') and time.perf_counter() - start > 0.3:
                return False
            key = self.render.text_input
            if key != -1:
                self.render.text_input = -1
                if key == 257:
                    return True
                elif key == 259:
                    text.text = text.text[:-1]
                else:
                    text.text += chr(key).lower()

class HomeUI(UI):
    def Start(self):
        super().Start()
        self.setup_layout()
        self.client.name = self.name_text.text
        self.client.login()

        # for comp in self.parent.components.values():
        #     comp.Active = False
        self.Active = True

    def setup_layout(self):

        # Background
        self.background = Box(center=(960, 540), size=(1920, 1080), color=(41, 128, 185), opacity=1, layer=0)
        self.render.add_ui_rect(self.background)

        # Title
        self.title = Text(text="Concrete Carnage", center=(960, 50), scale=1.5, color=(255, 200, 50), layer=1)
        self.render.add_text_rect(self.title)

        # Subtitle
        chosen_title = random.choice(titles)
        self.subtitle = Text(text=chosen_title, center=(960, 190), scale=1, color=(200, 200, 200))
        self.render.add_text_rect(self.subtitle)

        # Play Button
        self.play_button = Box(center=(960, 900), size=(250, 80), color=(76, 175, 80), opacity=0.9, clickable=True)
        self.render.add_ui_rect(self.play_button)
        self.play_text = Text(text="PLAY", center=(960, 900), scale=1, color=(255, 255, 255))
        self.render.add_text_rect(self.play_text)

        # Play With Friends Button
        self.friends_button = Box(center=(650, 900), size=(250, 80), color=(33, 150, 243), opacity=0.9, clickable=True)
        self.render.add_ui_rect(self.friends_button)
        # Top line
        self.friends_text1 = Text(text="PLAY WITH", center=(650, 885), scale=0.6, color=(255, 255, 255))
        self.render.add_text_rect(self.friends_text1)

        # Bottom line
        self.friends_text2 = Text(text="FRIENDS!", center=(650, 920), scale=0.6, color=(255, 255, 255))
        self.render.add_text_rect(self.friends_text2)

        # Game Mode Button
        self.mode_button = Box(center=(1270, 900), size=(250, 80), color=(156, 39, 176), opacity=0.9, clickable=True)
        self.render.add_ui_rect(self.mode_button)
        self.mode_text = Text(text="GAME MODE", center=(1270, 900), scale=0.5, color=(255, 255, 255))
        self.render.add_text_rect(self.mode_text)

        # Sign In Button (top right)
        self.signin_button = Box(center=(320, 300), size=(220, 60), color=(76, 175, 80), opacity=0.9, clickable=True)
        self.render.add_ui_rect(self.signin_button)
        self.signin_text = Text(text="name:", center=(100, 295), scale=1, color=(255, 255, 255))
        self.render.add_text_rect(self.signin_text)
        number = ''.join(str(random.randint(0, 9)) for _ in range(5))
        self.name_text = Text(text="Player" + number, center=(320, 300), scale=0.6, color=(255, 255, 255))
        self.render.add_text_rect(self.name_text)

        # Settings Button (top right)
        self.settings_button = Box(center=(1850, 950), size=(50, 50), color=(100, 100, 100), opacity=0.8,
                                   clickable=True)

        self.render.add_ui_rect(self.settings_button)
        self.settings_text = Text(text="⚙", center=(1850, 950), scale=3, color=(255, 255, 255))
        self.render.add_text_rect(self.settings_text)

        # Exit Button
        self.exit_button = Box(center=(1700, 950), size=(150, 60), color=(244, 67, 54), opacity=0.9, clickable=True)
        self.render.add_ui_rect(self.exit_button)

        self.exit_text = Text(text="EXIT", center=(1700, 950), scale=0.7, color=(255, 255, 255))
        self.render.add_text_rect(self.exit_text)

        # Weapon showcase boxes (decorative)
        weapon_colors = [(255, 140, 0), (255, 165, 0), (255, 100, 0), (255, 69, 0), (255, 50, 0), (255, 30, 0),
                         (200, 20, 0)]
        weapon_positions = [500, 650, 800, 960, 1120, 1270, 1420]

        self.weapon_boxes = []
        for i, (pos, color) in enumerate(zip(weapon_positions, weapon_colors)):
            box = Box(center=(pos, 780), size=(80, 60), color=color, opacity=0.8)
            self.render.add_ui_rect(box)
            self.weapon_boxes.append(box)

        # Mouse position tracking for button hover effects (optional)
        self.buttons = [self.play_button, self.friends_button, self.mode_button, self.signin_button,
                        self.settings_button, self.exit_button]
        self.button_colors = [btn.color for btn in self.buttons]
        self.mouse_over = None
        self.show = True


    def ButtonClicked(self, button):
        if button == self.play_button:
            self.activatePlaylayout()
        elif button == self.friends_button:
            self.activateFriendslayout()
        elif button == self.mode_button:
            pass
        elif button == self.signin_button:
            self.get_pressed_keys(self.name_text)
            self.client.name = self.name_text.text
        elif button == self.exit_button:
            self.parent.World.Exit()
            self.parent.destroy()
            self.client.logout()

    def activatePlaylayout(self):
        pwd = self.client.find_room()
        self.client.join_room(pwd)
        self.Active = False
        self.render.flush_ui()
        self.show = False
        self.parent.PlayUI.Active = True

    def activateFriendslayout(self):
        self.Active = False
        self.show = False
        self.parent.PlayWithFriends.Active = True

class PlayWithFriends(UI):
    def setup_layout(self):
        self.background = Box(center=(960, 540), size=(1920, 1080), color=(0, 0, 0), opacity=0.5, layer=3)
        self.render.add_ui_rect(self.background)

        # Main popup background
        self.popup = Box(
            center=(960, 500),
            size=(700, 420),
            color=(60, 170, 200),
            opacity=0.95,
            layer=5
        )
        self.render.add_ui_rect(self.popup)

        # Title
        self.title = Text(
            text="CREATE PRIVATE GAME",
            center=(860, 350),
            scale=0.8,
            color=(255, 255, 255),
            layer=6
        )
        self.render.add_text_rect(self.title)

        # Map preview box
        self.map_preview = Box(
            center=(780, 470),
            size=(260, 160),
            color=(120, 180, 200),
            opacity=1,
            layer=6
        )
        self.render.add_ui_rect(self.map_preview)

        self.map_text = Text(
            text="METAMORPH",
            center=(780, 470),
            scale=0.8,
            color=(255, 255, 255),
            layer=7
        )
        self.render.add_text_rect(self.map_text)

        # Game mode button
        self.mode_box = Box(
            center=(1080, 430),
            size=(250, 60),
            color=(120, 200, 220),
            opacity=1,
            clickable=True,
            layer=6
        )
        self.render.add_ui_rect(self.mode_box)

        self.mode_text = Text(
            text="GAME MODE\nFREE FOR ALL",
            center=(1080, 430),
            scale=0.45,
            color=(0, 50, 70),
            layer=7
        )
        self.render.add_text_rect(self.mode_text)

        # Server button
        self.server_box = Box(
            center=(1080, 510),
            size=(250, 60),
            color=(120, 200, 220),
            opacity=1,
            clickable=True,
            layer=6
        )
        self.render.add_ui_rect(self.server_box)

        self.server_text = Text(
            text="SERVERS\nGERMANY",
            center=(1080, 510),
            scale=0.45,
            color=(0, 50, 70),
            layer=7
        )
        self.render.add_text_rect(self.server_text)

        # Create Game button
        self.create_button = Box(
            center=(1080, 580),
            size=(250, 70),
            color=(50, 200, 100),
            opacity=1,
            clickable=True,
            layer=6
        )
        self.render.add_ui_rect(self.create_button)

        self.create_text = Text(
            text="CREATE GAME →",
            center=(1080, 580),
            scale=0.6,
            color=(255, 255, 255),
            layer=7
        )
        self.render.add_text_rect(self.create_text)

        # Join game section
        self.join_title = Text(
            text="JOIN GAME",
            center=(960, 650),
            scale=0.8,
            color=(255, 255, 255),
            layer=6
        )
        self.render.add_text_rect(self.join_title)

        # Code input box
        self.code_box = Box(
            center=(850, 710),
            size=(360, 60),
            color=(220, 220, 220),
            opacity=1,
            clickable=True,
            layer=6
        )
        self.render.add_ui_rect(self.code_box)

        self.code_text = Text(
            text="Enter your code",
            center=(850, 710),
            scale=0.5,
            color=(120, 120, 120),
            layer=7
        )
        self.render.add_text_rect(self.code_text)

        # Join button
        self.join_button = Box(
            center=(1110, 710),
            size=(180, 60),
            color=(70, 160, 200),
            opacity=1,
            clickable=True,
            layer=6
        )
        self.render.add_ui_rect(self.join_button)

        self.join_text = Text(
            text="Join Game!",
            center=(1110, 710),
            scale=0.55,
            color=(255, 255, 255),
            layer=7
        )
        self.render.add_text_rect(self.join_text)

        # Close button
        self.close_button = Box(
            center=(1280, 320),
            size=(40, 40),
            color=(200, 80, 80),
            opacity=1,
            clickable=True,
            layer=7
        )
        self.render.add_ui_rect(self.close_button)

        self.close_text = Text(
            text="X",
            center=(1280, 320),
            scale=0.8,
            color=(255, 255, 255),
            layer=8
        )
        self.render.add_text_rect(self.close_text)
        self.buttons = [self.close_button, self.join_button, self.code_box, self.create_button,
                        self.server_box]
        self.button_colors = [btn.color for btn in self.buttons]
        self.mouse_over = None
        self.show = True

    def ButtonClicked(self, button):
        if button == self.close_button:
            self.CloseLayout()
        elif button == self.code_box:
            self.EnterCode()
        elif button == self.join_button:
            self.client.login()
            self.joinRoom()
        elif button == self.create_button:
            self.client.login()
            self.CreatRoom()


    def CreatRoom(self):
        self.client.create_room()
        self.Active = False
        self.show = False
        self.render.flush_ui()
        time.sleep(0.1)
        self.parent.PlayUI.Active = True

    def joinRoom(self):
        self.client.join_room(self.code_text.text)
        self.Active = False
        self.show = False
        self.render.flush_ui()
        self.parent.PlayUI.Active = True

    def EnterCode(self):
        self.get_pressed_keys(self.code_text)
        self.client.room = self.code_text.text

    def CloseLayout(self):
        self.Active = False
        self.show = False
        self.render.flush_ui()
        self.parent.HomeUI.Active = True

class PlayUI(UI):
    def __init__(self):
        super(PlayUI, self).__init__()
        self.joined = False

    def Start(self):
        super().Start()

    def setup_layout(self):
        # Dark overlay background
        self.background = Box(center=(960, 540), size=(1920, 1080), color=(0, 0, 0), opacity=0.6, layer=5)
        # self.render.add_ui_rect(self.background)

        # Title
        self.title = Text(text="YOU WERE ELIMINATED",
                          center=(960, 300),
                          scale=1.2,
                          color=(255, 80, 80),
                          layer=6)
        self.render.add_text_rect(self.title)

        # Subtitle
        self.subtitle = Text(text="Prepare to re-enter the carnage",
                             center=(960, 380),
                             scale=0.6,
                             color=(200, 200, 200),
                             layer=6)
        self.render.add_text_rect(self.subtitle)

        # Respawn Button
        self.respawn_button = Box(center=(960, 520),
                                  size=(260, 80),
                                  color=(76, 175, 80),
                                  opacity=0.9,
                                  clickable=True,
                                  layer=6)
        self.render.add_ui_rect(self.respawn_button)

        self.respawn_text = Text(text="RESPAWN",
                                 center=(960, 520),
                                 scale=0.9,
                                 color=(255, 255, 255),
                                 layer=7)
        self.render.add_text_rect(self.respawn_text)

        # Main Menu Button
        self.menu_button = Box(center=(960, 630),
                               size=(260, 80),
                               color=(244, 67, 54),
                               opacity=0.9,
                               clickable=True,
                               layer=6)
        self.render.add_ui_rect(self.menu_button)

        self.menu_text = Text(text="MAIN MENU",
                              center=(960, 630),
                              scale=0.8,
                              color=(255, 255, 255),
                              layer=7)
        self.render.add_text_rect(self.menu_text)

        # Waiting text
        self.wait_text = Text(text="Respawning soon...",
                              center=(960, 720),
                              scale=0.5,
                              color=(180, 180, 180),
                              layer=6)
        self.render.add_text_rect(self.wait_text)

        # Chat background
        self.chat_background = Box(center=(300, 700),
                                   size=(500, 300),
                                   color=(20, 20, 20),
                                   opacity=0.8,
                                   layer=6)
        self.render.add_ui_rect(self.chat_background)

        # Chat title
        self.chat_title = Text(text="CHAT",
                               center=(300, 560),
                               scale=0.5,
                               color=(255, 255, 255),
                               layer=7)
        self.render.add_text_rect(self.chat_title)

        # Chat messages display
        self.chat_messages = Text(text="",
                                  center=(300, 690),
                                  scale=0.45,
                                  color=(220, 220, 220),
                                  layer=7)
        self.render.add_text_rect(self.chat_messages)

        # Chat input box
        self.chat_input_box = Box(center=(300, 830),
                                  size=(460, 50),
                                  color=(40, 40, 40),
                                  opacity=0.9,
                                  clickable=True,
                                  layer=7)
        self.render.add_ui_rect(self.chat_input_box)

        # Chat input text
        self.chat_input = Text(text="",
                               center=(300, 830),
                               scale=0.45,
                               color=(255, 255, 255),
                               layer=8)
        self.render.add_text_rect(self.chat_input)

        # Chat storage
        self.chat_log = []
        self.current_input = ""

        # Button tracking for hover
        self.buttons = [self.respawn_button, self.menu_button, self.chat_input_box]
        self.button_colors = [btn.color for btn in self.buttons]
        self.mouse_over = None
        self.show = True

    def ButtonClicked(self, button):
        if button == self.respawn_button:
            self.activateGamelayout()
        elif button == self.menu_button:
            self.activateMenulayout()
        elif button == self.chat_input_box:
            if self.get_pressed_keys(self.chat_input):
                if chat_filter.is_message_clean(self.chat_input.text):
                    self.add_chat_message()
                    # self.client.send_massage(self.chat_input.text)
                else:
                    self.chat_input.text = "*" * len(self.chat_input.text)
                    self.add_chat_message()
                    self.client.send_massage(self.chat_input.text)

    def add_chat_message(self):
        self.chat_log.append(self.chat_input.text)
        self.chat_input.text = ""

        # Keep last 6 messages
        self.chat_log = self.chat_log[-6:]

        self.chat_messages.text = "\n".join(self.chat_log)

    def activateMenulayout(self):
        self.Active = False
        self.show = False
        self.render.flush_ui()
        self.parent.HomeUI.Active = True
        self.client.logout()


    def activateGamelayout(self):
        self.Active = False
        self.show = False
        self.render.flush_ui()
        self.parent.GameUI.Active = True
        self.parent.PlayerController.Active = True
        self.client.Active = True
        self.client.respawn()


class GameUI(UI):

    def Update(self, dt):
        super().Update(dt)
        key = self.render.text_input
        if key != -1:
            if key == 256:
                self.Active = False
                self.show = False
                self.parent.PlayerController.Active = False
                self.parent.PlayUI.Active = True
                self.client.despawn()
            self.render.text_input = -1
