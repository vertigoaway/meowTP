from unittest import result

from netlib import recvUnencryptedFrame, sendUnencryptedFrame
from typing import Any
import socketserver
import threading
import logging
import time
logger = logging.getLogger(__name__)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    db: dict[Any, Any] = {"apple": 1648}
    dbLock = threading.Lock()  # lock for db

    pass


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):


    def query(self, data) -> tuple[int,dict[str, Any]]:

        key = data.get("k")

        if key is not None:
            val = self._queryKey(key)
            if val is None:
                return 404, {}

        else:

            val = data.get("v")
            key = self._queryVal(val)

        resp = {"k": key, "v": val}
        print(f"\tresp: {resp}")
        return 200, resp

    def _queryKey(self, key: str | int) -> Any | None:
        val = None
        with ThreadedTCPServer.dbLock:
            val = ThreadedTCPServer.db.get(key)
        return val

    def _queryVal(self, val: Any):
        key = []
        with ThreadedTCPServer.dbLock:
            raise NotImplementedError
        raise NotImplementedError

    def _write(self, key, val, replace=True) -> bool:
        with ThreadedTCPServer.dbLock:
            v = ThreadedTCPServer.db.get(key)
            if v is None:
                ThreadedTCPServer.db[key] = val
            elif replace:
                ThreadedTCPServer.db[key] = val
            else:
                return False
        return True

    def post(self, data: dict) -> tuple[int,dict[str, Any]]:
        k = data.get("k")
        v = data.get("v")
        if k is None or v is None:
            return 400, {}

        done = self._write(k, v, replace=False)
        if done:
            return 201, {}
        else:
            return 304, {}

    def push(self, data: dict) -> tuple[int,dict[str, Any]]:
        k = data.get("k")
        v = data.get("v")
        if k is None or v is None:
            return 400, {}

        done = self._write(k, v, replace=True)
        if done:
            return 201, {}
        else:
            return 304, {}

    def ping(self,data: dict) -> tuple[int,dict[str,Any]]:
        recvdTime : float = data['time']
        x = time.time()
        change = x-recvdTime
        logger.info(f'C->S ping:{(change)*1000}ms')
        return 200, {"time": x, "delta": change}

    def exists(self,data: dict) -> tuple[int,dict[str,Any]]:
        toCheck = data.get('k')
        if toCheck is None:
            return 400, {}
        with ThreadedTCPServer.dbLock:
            x = ThreadedTCPServer.db.get(toCheck)
        if x is not None:
            exist = True
        else:
            exist = False
        
        return 200, {"exists": exist}

    def unk(self, data) -> tuple[int, dict[Any, Any]]:
        return 400, {}
    
    COMMANDS = {
        "query": query,
        "post": post,
        "push": push,
        "ping": ping,
        "exists": exists,
        None: unk,
    }

    def handle(self):
        Running = True

        try:
            while Running:

                data = recvUnencryptedFrame(self.request)
                cmd = data["cmd"]
                logger.info(
                    f"{self.request.getpeername()} issued command {cmd}"
                )


                f = self.COMMANDS.get(cmd)
                if f is not None:
                    response = {}
                    statusCode, result = f(self,data=data[cmd])
                    response["id"] = data["id"]
                    response["status"] = statusCode
                    response["result"] = result
                else:
                    logger.error(
                        f"{self.request.getpeername()}: unknown command '{cmd}'"
                    )
                    response = {"status": 400, "result": {},"id":data["id"]}

                if Running:
                    sendUnencryptedFrame(self.request, response)
        except EOFError:
            # logger.warning(f"{self.request.getpeername()} dirty socket close")
            pass
        return

