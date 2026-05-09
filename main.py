from bereshit import Core
from MAP import server_map, main_game_object, client_map
from protocol import TICK

player = main_game_object()

Core.run([player] + client_map(), tick=TICK)
