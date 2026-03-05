from enum import IntEnum


class PacketType(IntEnum):
    INPUT = 1
    PING = 2
    PONG = 3
    STATE = 4


# struct formats for packets
CLIENT_PACK_FORMAT = "!BIIhhd"  # type, id, mask, dx, dy, dt
PING_FORMAT = "!BId"            # type, id, timestamp
PONG_FORMAT = "!Bd"             # type, timestamp
STATE_FORMAT = "!B10f"          # type + 10 floats: pos(3), quat(4), vel(3)
