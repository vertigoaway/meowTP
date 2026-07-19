import socket
from typing import Any, cast
from netlib import recvUnencryptedFrame, sendUnencryptedFrame
import logging
import time
logger = logging.getLogger(__name__)


class client:

    srv : tuple[str,int]
    sock : socket.socket
    frameId : int
    reqId : int
    def open(self, srv: tuple[str, int] | None = None):
        """Opens a socket connection to the server.
        Parameters:
         srv: Tuple containing hostname/ip and port number.
          Defaults to last used if left empty."""
        if isinstance(srv, type(None)):
            srv = self.srv
        self.srv = srv
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(srv)  # pyright: ignore[reportArgumentType]
        return

    def __init__(self, srv: tuple[str, int]):
        """Creates client object and opens a connection to the server.
        Parameters:
         srv: Tuple containing hostname/ip and port number.
        """
        self.open(srv)
        self.reqId = 1
        return
    
    def sendReq(self,req,responseExpected=True) -> dict[Any, Any]:
        req["id"] = self.reqId
        sendUnencryptedFrame(self.sock,req)
        self.reqId += 1
        if responseExpected:
            resp = recvUnencryptedFrame(self.sock)
        else:
            return {} # for the sake of my sanity

        return resp

    def query(self, key: str):
        """Find V corressponding to key arg in server.
        Parameters:
        key (Any): Key value of entry to query

        Returns:
         out: Value corresponding to key or status code if failed.
        """
        req = {"cmd": "query", "query": {"k": key}}
        received = self.sendReq(req)
        if received["status"] == 200:
            return received["result"]["v"]
        else:
            return None

    def search(self, val: Any) -> Any | int:
        """Find all keys containing val in server.
        Parameters:
        val (Any): Value to query

        Returns:
         out: Keys corresponding to val or status code if failed.
        """
        req = {"cmd": "query", "query": {"v": val}}
        received = self.sendReq(req)

        if received["status"] == 200:
            return received["result"]["k"]
        elif received["status"] == 400:
            logger.error(f"invalid search parameters!: {val}")
            raise TypeError
        else:
            return received["status"]

    def post(self, key: Any, value: Any, replace: bool = False) -> bool:
        """Post K-V pair to server.
        Parameters:
            key (Any): Key value of new entry.
            value (Any): Value of new entry.
            replace (bool): Replace existing values if present.
        Returns (bool):
         Whether or not data was written.
        """
        if replace:
            cmd: str = "push"
        else:
            cmd = "post"
        req = {"cmd": cmd, cmd: {"k": key, "v": value}}
        res = self.sendReq(req)["status"]
        if res == 201:
            return True
        elif res == 400:
            logger.error(f"invalid post parameters!: {req}")
            raise TypeError
        elif res == 304:
            return False
        return False
    def ping(self) -> float:
        """Pings server.

        Returns (float): 
         Difference between function call and first packet arrival on server side."""
        begin = time.time()
        req = {'cmd':'ping','ping': {'time':begin}}
        res = self.sendReq(req)['result']
        end = res['time']
        delta = res['delta']
        change = end - begin
        if change != delta:
            logger.critical(f'C->S ping delta mismatch! calculated: {change} received {delta}')
        logger.info(f'C->S ping: {change*1000}ms')
        return change
    def close(self) -> None:
        """Closes client socket."""
        logger.info(f"socket close fired")
        # resp = {"cmd": "quit"}
        # sendUnencryptedFrame(self.sock, resp)
        self.sock.close()
        return
