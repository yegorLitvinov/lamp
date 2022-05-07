import urandom
import utime

urandom.seed(utime.ticks_ms())


def randint(number: int) -> int:
    return urandom.getrandbits(32) % number
