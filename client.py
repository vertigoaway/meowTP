import lib, crypto, asyncio # pyright: ignore[reportMissingImports]
 
srv = ("127.0.0.1",lib.udpPort)

def interface(msgs):
    print("enter a request!\nDownload:\n\tdownFi <filename>\nUpload:\n\tupldFi <filename>\nQuit:\n\tquit")
    cmd = input("meowtp:")
    req = cmd[0:6]
    param = cmd[7:]
    match req:
        case "downFi":
            cmd = cmd.replace("/","").strip()
            msgs.append(b"downFi"+bytes(param,'utf-8'))
            msgs.append(b"sizeOf"+bytes(param,'utf-8'))
            file = {"expectingFile":True,"name":param,"sectors":{}}
        case "upldFi":
            cmd = cmd.replace("/","")
            msgs.append(cmd.encode())
            file = {"sendingFile":True,"name":param,"sectors":lib.disassembleFile(param)} 
            #TODO: finish upload implementation
        case "quit":
            global quit
            quit = True
            msgs.append(b"stpNow")
            file = {"expectingFile":False}
        case _:
            print("err:"+req)
            raise Exception("invalid command")
        
    return msgs,file



#begin connection
class CliMtpProto:
    def __init__(self):
        self.privKey, self.pubKey, self.pem = crypto.createKeyPair()
        self.encrypt = False
        self.skimp = False
        self.srvPubKey = None
        self.file = {"expectingFile":False}
        self.msgs = []
        self.nonce = 0 #goes at start of all cmds
    def connection_made(self, transport):
        self.transport = transport
        print('connection established')
        transport.sendto(self.nonce.to_bytes(4,'big')+b"reqKey"+self.pem, (srv))
        self.nonce+=1
    def datagram_received(self, data, addr):
        encrypt = self.encrypt 
        skimp = self.skimp 
        srvPubKey = self.srvPubKey
        file = self.file 
        msgs = self.msgs 
        pktNonce,req,param = lib.parseRawPkts([data], encrypted=encrypt, privKey=self.privKey)[0]
        if pktNonce!=self.nonce:
            print("reported nonce different than current nonce, somethings out of order :(")
        match req:
            ### key exchange ###
            case b"reqKey":# we recieve server key and get requested for client key
                skimp = True
                srvPubKey = crypto.recvPubkey(param)
                msgs.append(b"finKey")
            case b"finKey":#ensure both can read messages
                print("key exchange completed")
                msgs.append(b"ready!")
            case b"ready!": #idle
                msgs,file = interface(msgs)
            case b"sizeOf":
                if file["expectingFile"]:
                    file["size"] = int.from_bytes(param,'big',signed=False)
                return
            case b"partFi": #download a "sector" of file
                if file["expectingFile"]:
                    sectNo = int.from_bytes(param[0:6],"big")
                    contents = param[7:]
                    file["sectors"][sectNo] = contents
            case b"finish":
                if file["expectingFile"] and len(file["sectors"])>=int.from_bytes(param[0:6],"big"):

                    lib.assembleFile(file["sectors"],file["name"])
                    file = {"expectingFile":False}
            case b"err400": #exception
                if file["expectingFile"]:
                    print("400: doesn't exist / you are not authorized")
                    file["expectingFile"] = {"expectingFile":False}
                    interface(msgs)

            case _:
                print("invalid request recieved D:")
                print(req)
        

        if len(msgs) != 0:
            self.nonce = lib.sendMessages(self,srv, msgs, encrypt=encrypt, publicKey=srvPubKey,nonce=self.nonce)
        else:
            if file["expectingFile"] == False:
                self.nonce = lib.sendMessages(self,srv, [b"ready!"], encrypt=encrypt,publicKey=srvPubKey,nonce=self.nonce)
            else:
                pass
        if skimp: #lazy? yeah lol
            encrypt = True
            skimp = False

        self.encrypt = encrypt
        self.skimp = skimp
        self.srvPubKey = srvPubKey
        self.file = file
        self.msgs = []
    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection lost D:")



async def main():

    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: CliMtpProto(),
        remote_addr=srv)

    try:
        await on_con_lost
    finally:
        transport.close()


asyncio.run(main())