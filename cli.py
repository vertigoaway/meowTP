import socket
from typing import Any, cast
from netlib import recvUnencryptedFrame, sendUnencryptedFrame


class client:
    def open(self, srv: tuple[str, int] | None = None):
        if isinstance(srv, type(None)):
            srv = self.srv
        self.srv = srv
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(srv)  # pyright: ignore[reportArgumentType]
        return

    def __init__(self, srv: tuple[str, int]):
        self.open(srv)
        return

    def query(self, key: str):
        """Find V corressponding to key arg in server.
        Parameters:
        key (Any): Key value of entry to query

        Returns:
         out: Value corresponding to key or status code if failed. 
        """
        req = {"cmd": "query",
                "query":{'k':key}}
        sendUnencryptedFrame(self.sock, req)
        received = recvUnencryptedFrame(self.sock)
        if received['status'] == 200:
            return received['result']['v']
        else:
            return received['status']
    
    def search(self,val: Any) -> Any | int:
        """Find all keys containing val in server.
        Parameters:
        val (Any): Value to query

        Returns:
         out: Keys corresponding to val or status code if failed. 
        """
        req = {"cmd": "query",
                "query":{'v':val}}
        sendUnencryptedFrame(self.sock,req)
        received = recvUnencryptedFrame(self.sock)

        if received['status'] == 200:
            return received['result']['k']
        elif received['status'] == 400:
            raise TypeError
        else:
            return received['status']

    def post(self, key: Any, value: Any, replace : bool = False) -> bool: 
        """Post K-V pair to server.
        Parameters:
            key (Any): Key value of new entry.
            value (Any): Value of new entry.
            replace (bool): Replace existing values if present.
        Returns (bool):
         Whether or not data was written.
        """
        if replace:
            cmd : str = 'push'
        else:
            cmd = 'post'
        req = {"cmd": cmd, 
               cmd: 
                    {'k':key,
                     'v':value}}
        sendUnencryptedFrame(self.sock, req)

        res = recvUnencryptedFrame(self.sock)['status']
        if res == 201:
            return True
        elif res is 400:
            raise TypeError
        elif res is 304:
            return False
        return False

    def close(self) -> None:
        """Closes client socket."""
        #resp = {"cmd": "quit"}
        #sendUnencryptedFrame(self.sock, resp)
        self.sock.close()
        return
