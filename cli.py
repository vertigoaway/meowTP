import socket
from typing import Any, NoReturn, cast
from netlib import recvUnencryptedFrame, sendUnencryptedFrame
import logging
from concurrent.futures import Future
import threading
import time
from typing import Literal, overload
logger = logging.getLogger(__name__)


class client:

    srv : tuple[str,int]
    sock : socket.socket
    frameId : int
    reqId : int
    pending : dict[int,Future] = {}
    def _nextId(self) -> int:
        self.reqId+=1
        return self.reqId
    
    @overload
    def sendReq(self, request, responseExpected : Literal[True] = True) -> Future: ...

    @overload
    def sendReq(self, request, responseExpected : Literal[False]) -> None: ...

    def sendReq(self, request,responseExpected=True) -> Future | None:
        id = self._nextId()
        request["id"] = id
        if responseExpected:
            future = Future()
            self.pending[id] = future
        else:
            future = None
        sendUnencryptedFrame(self.sock,request)        
        return future
    
    def dispatch(self) -> NoReturn:
        while True:
            response = recvUnencryptedFrame(self.sock)
            id = response["id"]

            future = self.pending.pop(id,None)

            if future is None:
                logger.warning(
                    "Recieved response for unknown request %d",
                    id
                )
                continue
            future.set_result(response)
    
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
        self.dispatchThread = threading.Thread(target=self.dispatch)
        self.dispatchThread.start()
        return

    def __init__(self, srv: tuple[str, int]):
        """Creates client object and opens a connection to the server.
        Parameters:
         srv: Tuple containing hostname/ip and port number.
        """
        self.open(srv)
        self.reqId = 1
        return

    def query(self, key: str):
        """Find V corressponding to key arg in server.
        Parameters:
        key (Any): Key value of entry to query

        Returns:
         out: Value corresponding to key or status code if failed.
        """
        req = {"cmd": "query", "query": {"k": key}}
        received = self.sendReq(req)
        received = received.result(timeout=5)
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
        received = received.result(timeout=5)

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
        res = self.sendReq(req)
        res = res.result(timeout=5)
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
        res = self.sendReq(req)
        res = res.result(timeout=5)['result']
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
