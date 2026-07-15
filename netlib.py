import compression.zstd as zstd
import base64
from typing import Any
from typing import cast
import msgpack as msgP
ENCODING = 'utf8'

def serializeBytes(data: bytes) -> str:
    return base64.b64encode(data).decode(ENCODING)


def deserializeBytes(data: str) -> bytes:
    return base64.b64decode(data)


def compress(data: dict,level : int = 3) -> bytes:
    """Messagepack and Zstd compress dict
    Parameters:
        data (dict): data to be packed and compressed.
        level (int): Zstd level of compression.

    Returns (bytes):
     Compressed and packed bytes.
    """
    encodedData = cast(bytes,msgP.dumps(data))
    return zstd.compress(encodedData, level)


def decompress(data: bytes) -> dict:
    """un-Messagepack and Zstd decompress.
    Parameters:
        data (bytes): Packed and compresssed bytes.

    Returns (dict):
     Decompressed data.
    """
    decodedData = zstd.decompress(data)
    result = cast(dict,msgP.loads(decodedData))
    return result


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
    payl = recvExact(sock, length)
    return decompress(payl)


def sendUnencryptedFrame(sock, payload) -> None:
    payload = compress(payload)
    sock.sendmsg([len(payload).to_bytes(4, "big"),
                  payload])
    return


if __name__ == "__main__":
    ENCODING = "utf8"
