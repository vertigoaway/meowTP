from netlib import recvUnencryptedFrame, sendUnencryptedFrame
from typing import Any
import socketserver
import threading

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    db : dict[Any,Any]= {'apple':1648}
    dbLock = threading.Lock()
    
    
    def query(self, data) -> dict[Any, Any]:
        
        print(f"{data}")
        key = data.get('k')

        if key is not None:
            val = self.queryKey(key)    
            if val is None:
                return {"status":404}

        else:

            val = data.get('v')
            key = self.queryVal(val)


        resp = {"status": 200, 
                'query': 
                    {'k': key, 
                     'v': val}}
        print(f"\tresp: {resp}")
        return resp

    def queryKey(self, key: str|int) -> Any | None:
        val = None
        if self.dbLock.acquire():
            val = self.db.get(key)
        self.dbLock.release()
        return val

    def queryVal(self, val: Any):
        key = []
        if self.dbLock.acquire():
            raise NotImplemented
        self.dbLock.release()
        raise NotImplemented
    def write(self,key,val,replace=True):
        if self.dbLock.acquire():
            v = self.db.get(key)
            if v is None:
                self.db[key] = val
            elif replace == True:
                self.db[key] = val
            else:
                return False
        self.dbLock.release()
        return True
    def post(self, data: dict) -> dict[str, int]:
        print(data)
        k = data.get('k')
        v = data.get('v')
        if k == None or v == None:
            return {'status':400}

        done = self.write(k,v,replace=False)
        if done:

            return {"status": 201}
        else:
            return {'status': 304}
    def push(self,data: dict) -> dict[str, int]:
        k = data.get('k')
        v = data.get('v')
        if k == None or v == None:
            return {'status':400}

        done = self.write(k,v,replace=True)
        if done:
            return {"status":201}
        else:
            return {'status':304}
    def unk(self, data) -> dict[str, int]:
        response = {"status": 400}
        return response

    def handle(self):
        Running = True
        cmds = {
            "query": self.query,
            "post": self.post,
            "push": self.push,
            None: self.unk,
        }
        try:
            while Running:
                
                data = recvUnencryptedFrame(self.request)
                cmd = data.get("cmd")

                print(str(cmd) + ":\n\t", end="")



                f = cmds.get(cmd)
                if f is not None:
                    response = f(data.get(cmd,data))
                else:
                    response = {"status": 400}
                
                if Running:
                    sendUnencryptedFrame(self.request, response)
        except EOFError:
            pass
        return