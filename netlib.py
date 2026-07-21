import logging
from typing import Any, Literal
from typing import cast
import base64
import compression.zstd as zstd
import msgpack as msgP

ENCODING = "utf8"
ENDIAN: Literal["big", "little"] = "big"
MAX_FRAME = 64 * 1024 * 1024
MIN_COMPRESS_SIZE = 128
FLAG_SIZE = 1  # 1 = 8 bits
FRAME_LENGTH_INT_BYTES = 4  # 4 = 32 bits

logger = logging.getLogger(__name__)


# def serializeBytes(data: bytes) -> str:
#    return base64.b64encode(data).decode(ENCODING)


# def deserializeBytes(data: str) -> bytes:
#    return base64.b64decode(data)


def flag_decode(byte: bytes) -> list[bool]:
    """Converts byte flag into list of bools representing each bit."""
    x = int.from_bytes(byte, ENDIAN)
    decoded = []
    for i in range(0, FLAG_SIZE * 8):
        decoded.append(x & (1 << i))
    return cast(list[bool], decoded)


def flag_encode(options: list[bool]) -> int:
    """Converts list of bools representing each bit into byte flag."""
    if len(options) == FLAG_SIZE * 8:
        out = 0x00
        for i, o in enumerate(options):
            out |= o << i
    else:
        raise ValueError
    return out


# compress and decompress need a better name lol
def compress(data: dict, level: int = 9) -> tuple[bytes, int]:
    """Messagepack and Zstd compress dict
    Parameters:
        data (dict): data to be packed and compressed.
        level (int): Zstd level of compression.

    Returns (bytes):
     Compressed and packed bytes.
    """
    opts = [False, False, False, False, False, False, False, False] * FLAG_SIZE
    packed = cast(bytes, msgP.dumps(data))
    if len(packed) >= MIN_COMPRESS_SIZE:
        logger.debug("%s exceeds 128, compressing frame with Zstd", len(packed))
        opts[0] = True

    flags = flag_encode(opts)

    if opts[0]:
        packed = zstd.compress(packed, level)

    return (packed, flags)


def decompress(data: bytes, zstd_enabled: bool = True) -> dict:
    """un-Messagepack and Zstd decompress.
    Parameters:
        data (bytes): Packed and compresssed bytes.
        zstdEnabled (bool): Enables or disables ZSTD decompression

    Returns (dict):
     Decompressed data.
    """
    if zstd_enabled:
        decompressed_data = zstd.decompress(data)
        logger.debug(
            " compressed: %s | decompressed: %s", len(data), len(decompressed_data)
        )
    else:
        decompressed_data = data
    unpacked_data = cast(dict, msgP.loads(decompressed_data))
    return unpacked_data


def recv_exact(sock, n) -> bytes:
    """Recieves exact number of bytes specified.

    Parameters:
        sock: Socket to receive from.
        n: Number of bytes to receive."""
    data = bytearray()
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise EOFError
        data.extend(chunk)
    return bytes(data)


def recv_unencrypted_frame(sock) -> dict[Any, Any]:
    length = int.from_bytes(recv_exact(sock, FRAME_LENGTH_INT_BYTES), ENDIAN)

    if length > MAX_FRAME:
        logger.error("frame length %sbytes sent exceeds %s!", length, MAX_FRAME)
        raise ValueError("Frame too large!")
    flags = flag_decode(recv_exact(sock, FLAG_SIZE))
    payl = recv_exact(sock, length)
    if flags[0]:  # compression enabled
        res = decompress(payl, zstd_enabled=True)
    else:
        res = decompress(payl, zstd_enabled=False)
    return res


def send_unencrypted_frame(sock, payload) -> None:
    logger.debug("sending frame with payload: %s", payload)
    frame, flags = compress(payload)
    sock.sendmsg(
        [
            len(frame).to_bytes(FRAME_LENGTH_INT_BYTES, ENDIAN),
            flags.to_bytes(FLAG_SIZE, ENDIAN),
            frame,
        ]
    )
    return


if __name__ == "__main__":
    ENCODING = "utf8"
