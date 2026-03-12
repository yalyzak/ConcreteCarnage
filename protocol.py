from enum import IntEnum


class PacketType(IntEnum):
    INPUT = 1
    PING = 2
    PONG = 3
    STATE = 4
    DAMAGE = 5
    RESPAWN = 6
    DESPAWN = 7

# struct formats for packets

CLIENT_PACK_FORMAT = "!BIIhhd"  # type, id, mask, dx, dy, dt
PING_FORMAT = "!BId"            # type, id, timestamp
PONG_FORMAT = "!Bd"             # type, timestamp
STATE_FORMAT = "!BI10f"         # type + id + 10 floats: id, pos(3), quat(4), vel(3)
DAMAGE_FORMAT = "!B1f"          # type + HP
SPAWN_FORMAT = "!BI"             # type + id

TICK = 1/30