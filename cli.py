import logging
from concurrent.futures import Future
import threading
import time
from typing import Literal, overload, Any, cast
import socket
from netlib import recv_unencrypted_frame, send_unencrypted_frame

logger = logging.getLogger(__name__)
MAX_TIMEOUT = 1


class Client:
    """MeowTP client object."""

    srv: tuple[str, int]
    sock: socket.socket
    frameId: int
    req_id: int
    pending: dict[int, Future] = {}

    def _next_id(self) -> int:
        self.req_id += 1
        return self.req_id

    @overload
    def send_req(self, request, response_expected: Literal[True] = True) -> Future:
        ...

    @overload
    def send_req(self, request, response_expected: Literal[False]) -> None:
        ...

    def send_req(self, request, response_expected=True) -> Future | None:
        cur_id = self._next_id()
        request["id"] = cur_id
        if response_expected:
            future: Future | None = Future()
            self.pending[cur_id] = cast(Future, future)
        else:
            future = None
        send_unencrypted_frame(self.sock, request)
        return future

    def dispatch(self) -> None:
        """Receiving thread"""
        while self.connected:
            try:
                response = recv_unencrypted_frame(self.sock)
            except OSError:  # socket is closed
                continue
            cur_id = response["id"]

            future = self.pending.pop(cur_id, None)

            if future is None:
                logger.warning("Recieved response for unknown request %d", cur_id)
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
        self.connected = True
        self.dispatch_thread = threading.Thread(target=self.dispatch)
        self.dispatch_thread.start()

    def __init__(self, srv: tuple[str, int]):
        """Creates client object and opens a connection to the server.
        Parameters:
         srv: Tuple containing hostname/ip and port number.
        """
        self.open(srv)
        self.req_id = 1

    def query(self, key: str):
        """Find V corressponding to key arg in server.
        Parameters:
        key (Any): Key value of entry to query

        Returns:
         out: Value corresponding to key or status code if failed.
        """
        req = {"cmd": "query", "query": {"k": key}}
        fut = self.send_req(req)
        received: dict[str, Any] = fut.result(timeout=MAX_TIMEOUT)
        if received["status"] == 200:
            return received["result"]["v"]
        return None

    def search(self, val: Any) -> Any | int:
        """Find all keys containing val in server.
        Parameters:
        val (Any): Value to query

        Returns:
         out: Keys corresponding to val or status code if failed.
        """
        req = {"cmd": "query", "query": {"v": val}}
        fut = self.send_req(req)
        received: dict[str, Any] = fut.result(timeout=MAX_TIMEOUT)

        if received["status"] == 200:
            return received["result"]["k"]
        if received["status"] == 400:
            logger.error("invalid search parameters!: %s", val)
            raise TypeError
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
        res = self.send_req(req)
        res = res.result(timeout=5)
        if res == 201:
            return True
        if res == 400:
            logger.error("invalid post parameters!: %s", req)
            raise TypeError
        if res == 304:
            return False
        return False

    def exists(self, key: Any) -> bool:
        """Check for the existence of an entry.

        Parameters:
         key (Any): Entry to check for existence.

        Returns (bool):
         Whether or not an entry is defined with key var."""
        req = {"cmd": "exists", "exists": {"k": key}}
        fut = self.send_req(req)
        res: dict[str, Any] = fut.result(timeout=MAX_TIMEOUT)
        exist = res["result"]["exists"]
        return exist

    def delete(self, key: Any) -> bool:
        """Delete entry specified with key.

        Parameters:
            key (Any): Entry to delete.

        Returns (bool):
         Whether or not an entry was deleted.
        """
        req = {"cmd": "del", "del": {"k": key}}

        fut = self.send_req(req)
        res: dict[str, Any] = fut.result(timeout=MAX_TIMEOUT)

        deleted = res["result"]["deleted"]
        return deleted

    def ping(self) -> float:
        """Pings server.

        Returns (float):
         Difference between function call and first packet arrival on server side."""
        begin = time.time()
        req = {"cmd": "ping", "ping": {"time": begin}}
        fut = self.send_req(req)
        res: dict[str, Any] = fut.result(timeout=MAX_TIMEOUT)["result"]
        end = res["time"]
        delta = res["delta"]
        change = end - begin
        if change != delta:
            logger.critical(
                "C->S ping delta mismatch! calculated: %s received %s", change, delta
            )
        logger.info("C->S ping: %sms", change * 1000)
        return change

    def close(self) -> None:
        """Closes client socket."""
        logger.info("socket close fired")
        # resp = {"cmd": "quit"}
        # sendUnencryptedFrame(self.sock, resp)
        self.connected = False
        self.sock.close()
