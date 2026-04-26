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
    HEADER = 9
    LOGIN = 10


def PacketFormat(case):
    """Return struct format string for packet type."""
    switch_PacketFormat = {
        1: "Ihhd",
        2: "d",
        3: "Bd",
        4: "10f",
        5: "1f",
        6: "",
        7: "",
        9: "!BI16sI",
        10: "!I16s32s",

    }
    return switch_PacketFormat.get(case)

# struct formats for packets

HEADER_FORMAT = "!BI16sI"  # type + id + token + seq
CLIENT_INPUT_FORMAT = "!Ihhd"  # mask, dx, dy, dt
PING_FORMAT = "!d"             # timestamp
PONG_FORMAT = "!Bd"            # type, timestamp (no header)
STATE_FORMAT = "!10f"          # pos, qwd, vel
DAMAGE_FORMAT = "!1f"          # HP


SIGNATURE_FORMAT = "32s"
SIGNATURE_SIZE = 32
SESSION_TIMEOUT = 120

TICK = 1/30



