import compression.zstd as zstd
import base64
from multiprocessing import Value
from typing import Any
from typing import cast
import msgpack as msgP
ENCODING = 'utf8'
MAX_FRAME = 64 * 1024 * 1024
def serializeBytes(data: bytes) -> str:
    return base64.b64encode(data).decode(ENCODING)


def deserializeBytes(data: str) -> bytes:
    return base64.b64decode(data)

# compress and decompress need a better name lol
def compress(data: dict, level : int = 9) -> tuple[bytes,int]:
    """Messagepack and Zstd compress dict
    Parameters:
        data (dict): data to be packed and compressed.
        level (int): Zstd level of compression.

    Returns (bytes):
     Compressed and packed bytes.
    """
    flags = 0b00000000    
    packed = cast(bytes,msgP.dumps(data))
    if len(packed) >= 128:
        print('c')
        flags |= (1 << 0)
        packed = zstd.compress(packed, level)
    
    return (packed,flags)


def decompress(data: bytes,zstdEnabled: bool = True) -> dict: 
    """un-Messagepack and Zstd decompress.
    Parameters:
        data (bytes): Packed and compresssed bytes.

    Returns (dict):
     Decompressed data.
    """
    if zstdEnabled:
        decompressedData = zstd.decompress(data)
        print(f"\tcompressed:{len(data)}\n\tdecompressed{len(decompressedData)}")
    else:
        decompressedData = data
    unpackedData = cast(dict,msgP.loads(decompressedData))
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
    length = int.from_bytes(recvExact(sock, 4), "big")
    if length > MAX_FRAME:
        raise ValueError("Frame too large!")
    flags = int.from_bytes(recvExact(sock,1),'big')
    payl = recvExact(sock, length)
    if flags & (1 << 0): #compression enabled
        res = decompress(payl,zstdEnabled=True)
    else:
        res = decompress(payl, zstdEnabled=False)
    return res


def sendUnencryptedFrame(sock, payload) -> None:
    frame,flags = compress(payload)
    sock.sendmsg([len(frame).to_bytes(4, "big"),
                  flags.to_bytes(1,"big"),
                  frame])
    return


if __name__ == "__main__":
    ENCODING = "utf8"
