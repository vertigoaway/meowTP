import compression.zstd as zstd
import base64
from typing import Any
from typing import cast
import msgpack as msgP
import logging

ENCODING = "utf8"
ENDIAN = "big"
MAX_FRAME = 64 * 1024 * 1024
MIN_COMPRESS_SIZE = 128
FLAG_SIZE = 1  # 1 = 8 bits
FRAME_LENGTH_INT_BYTES = 4  # 4 = 32 bits

logger = logging.getLogger(__name__)


#def serializeBytes(data: bytes) -> str:
#    return base64.b64encode(data).decode(ENCODING)


#def deserializeBytes(data: str) -> bytes:
#    return base64.b64decode(data)


def flagDecode(byte:bytes) -> list[bool]:
    x = int.from_bytes(byte,ENDIAN)
    decoded = []
    for i in range(0,FLAG_SIZE*8):
        decoded.append(x & (1 << i))
    return cast(list[bool],decoded)


def flagEncode(options: list[bool]) -> int:
    if len(options) == FLAG_SIZE*8:
        out = 0x00
        for i,o in enumerate(options):
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
    opts = [False,False,False,False,False,False,False,False]*FLAG_SIZE
    packed = cast(bytes, msgP.dumps(data))
    if len(packed) >= MIN_COMPRESS_SIZE:
        logger.debug(f"{len(packed)} exceeds 128, compressing frame with Zstd")
        opts[0] = True
    
    flags = flagEncode(opts)

    if opts[0]:
        packed = zstd.compress(packed, level)

    return (packed, flags)


def decompress(data: bytes, zstdEnabled: bool = True) -> dict:
    """un-Messagepack and Zstd decompress.
    Parameters:
        data (bytes): Packed and compresssed bytes.
        zstdEnabled (bool): Enables or disables ZSTD decompression

    Returns (dict):
     Decompressed data.
    """
    if zstdEnabled:
        decompressedData = zstd.decompress(data)
        logger.debug(
            f" compressed: {len(data)} | decompressed: {len(decompressedData)}"
        )
    else:
        decompressedData = data
    unpackedData = cast(dict, msgP.loads(decompressedData))
    return unpackedData


def recvExact(sock, n) -> bytes:
    data = bytearray()
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise EOFError
        data.extend(chunk)
    return bytes(data)


def recvUnencryptedFrame(sock) -> dict[Any, Any]:
    length = int.from_bytes(recvExact(sock, FRAME_LENGTH_INT_BYTES), ENDIAN)

    if length > MAX_FRAME:
        logger.error(f"frame length {length}bytes sent exceeds {MAX_FRAME}!")
        raise ValueError("Frame too large!")
    flags = flagDecode(recvExact(sock, FLAG_SIZE))
    payl = recvExact(sock, length)
    if flags[0]:  # compression enabled
        res = decompress(payl, zstdEnabled=True)
    else:
        res = decompress(payl, zstdEnabled=False)
    return res


def sendUnencryptedFrame(sock, payload) -> None:
    logger.debug(f"sending frame with payload: {payload}")
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
