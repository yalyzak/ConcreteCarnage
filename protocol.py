from enum import IntEnum


class PacketType(IntEnum):
    INPUT = 1
    PING = 2
    PONG = 3
    STATE = 4
    DAMAGE = 5
    RESPAWN = 6
    DESPAWN = 7
    CREATE = 8

# struct formats for packets

CLIENT_PACK_FORMAT = "!BI16s2Ihhd"  # type, id, token, seq, mask, dx, dy, dt
PING_FORMAT = "!BI16sId"            # type, id, token, seq, timestamp
PONG_FORMAT = "!Bd"             # type, timestamp
STATE_FORMAT = "!BI10f"         # type + id + 10 floats: id, pos(3), quat(4), vel(3)
DAMAGE_FORMAT = "!B1f"          # type + HP
SPAWN_FORMAT = "!BI"             # type + id

SIGNATURE_FORMAT = "32s"
SIGNATURE_SIZE = 32
SESSION_TIMEOUT = 120
LOGIN_FORMAT = "!I16s32s"
TICK = 1/30