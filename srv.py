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

    def query(self, data) -> dict[Any, Any]:

        key = data.get("k")

        if key is not None:
            val = self.queryKey(key)
            if val is None:
                return {"status": 404, "result": {}}

        else:

            val = data.get("v")
            key = self.queryVal(val)

        resp = {"status": 200, "result": {"k": key, "v": val}}
        print(f"\tresp: {resp}")
        return resp

    def queryKey(self, key: str | int) -> Any | None:
        val = None
        with ThreadedTCPServer.dbLock:
            val = ThreadedTCPServer.db.get(key)
        return val

    def queryVal(self, val: Any):
        key = []
        with ThreadedTCPServer.dbLock:
            raise NotImplementedError
        raise NotImplementedError

    def write(self, key, val, replace=True):
        with ThreadedTCPServer.dbLock:
            v = ThreadedTCPServer.db.get(key)
            if v is None:
                ThreadedTCPServer.db[key] = val
            elif replace:
                ThreadedTCPServer.db[key] = val
            else:
                return False
        return True

    def post(self, data: dict) -> dict[str, Any]:
        print(data)
        k = data.get("k")
        v = data.get("v")
        if k is None or v is None:
            return {"status": 400, "result": {}}

        done = self.write(k, v, replace=False)
        if done:
            return {"status": 201, "result": {}}
        else:
            return {"status": 304, "result": {}}

    def push(self, data: dict) -> dict[str, Any]:
        k = data.get("k")
        v = data.get("v")
        if k is None or v is None:
            return {"status": 400, "result": {}}

        done = self.write(k, v, replace=True)
        if done:
            return {"status": 201, "result": {}}
        else:
            return {"status": 304, "result": {}}

    def ping(self,data: dict) -> dict[str,Any]:
        recvdTime : float = data['time']
        x = time.time()
        change = x-recvdTime
        logger.info(f'C->S ping:{(change)*1000}ms')
        res = {"status": 200, "result": { "time": x, "delta": change}}
        return res

    def unk(self, data) -> dict[str, int]:
        response = {"status": 400, "result": {}}
        return response
    
    COMMANDS = {
        "query": query,
        "post": post,
        "push": push,
        'ping': ping,
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

                print(str(cmd) + ":\n\t", end="")

                f = self.COMMANDS.get(cmd)
                if f is not None:
                    response = f(self,data=data[cmd])
                    response["id"] = data["id"]
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

