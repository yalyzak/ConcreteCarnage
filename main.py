from bereshit import Core
from MAP import server_map, main_game_object
from protocol import TICK

player = main_game_object()

Core.run([player] + server_map(), tick=TICK)
