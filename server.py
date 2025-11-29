import lib, socketserver, cryptography # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives.asymmetric import rsa # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import serialization # pyright: ignore[reportMissingImports] QUIET!!!
from cryptography.hazmat.primitives.asymmetric import padding# pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import hashes# pyright: ignore[reportMissingImports]

def recvPubkey(param):
    clientPK = serialization.load_pem_public_key(param.encode("utf-8"))
    return clientPK
class UDPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request[0]
        sock = self.request[1]
        print(f"{self.client_address[0]} connected!")


        try: 
            if keychain[self.client_address[0]]["encrypt"]:
                clientPK = keychain[self.client_address[0]]["clientPK"]#key was exchanged, assume all messages are encrypted
                data = lib.privKeyDecrypt(data,privKey)
        except:
            keychain[self.client_address[0]] = {"encrypt":False} #no key exchanged, note it down
        encrypt = keychain[self.client_address[0]]["encrypt"]
        try:
            data = data.decode("utf-8").strip()
        except:
            1+1
        tmp, req, param = data.split(" ", 2)

        if tmp!="meowtp" and not encrypt:
            print("not a meowtp client, throwing connection out")
            exit()
        tmp=None
        print("matching: "+req)
        req = req.strip()
        match req:
            case "hand?":
                msg = "meowtp hand "+pem.decode("utf-8")
            case "shake?":
                keychain[self.client_address[0]] = {"clientPK":recvPubkey(param),
                                                "encrypt":True}
                encrypt = True
                clientPK = keychain[self.client_address[0]]["clientPK"]
                msg = "meowtp shake "+self.client_address[0]
            case "meow":
                msg = "meowtp await ?"
            case "up":
                param = str(param.split("/")[-1::])

            case "down":
                param = param.split(" ")
                sector = param[0].strip()
                param = param.pop()
                fileName = str(param.split("/")[-1::][0])
                msg = lib.readSector(fileName,sector).decode("utf-8")
                msg = "meowtp down "+msg
            case _:
                msg = "meowtp null ?"

        if keychain[self.client_address[0]]["encrypt"]:
            print(len(msg))
            msg = lib.pubKeyEncrypt(msg.encode("utf-8"),clientPK)
        else:
            msg = msg.encode("utf-8")
        sock.sendto(msg, self.client_address)



if __name__ == "__main__":
    with socketserver.UDPServer(("127.0.0.1", lib.udpPort), UDPHandler) as server:
        print("server up!")

        privKey, pubKey, pem = lib.createKeyPair()
        keychain = {}
        server.serve_forever()