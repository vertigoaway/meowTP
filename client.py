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

class commands:
    def __init__():
        pass
    def reqKey(msgs,param):
        srvPubKey = crypto.recvPubkey(param)
        srvPubKey = srvPubKey
        skimp = True
        msgs.append(b"finKey")
        return msgs,srvPubKey,skimp
    def finKey(msgs):
        print("key exchange completed")
        msgs.append(b"ready!")
        return msgs
    def ready(msgs):
        msgs,file = interface(msgs)
        return msgs,file
    def sizeOf(file,param):
        if file["expectingFile"]:
            file["size"] = int.from_bytes(param,'big')
            
        return file,param
    def partFi(file,param):
        if file["expectingFile"]:
            sectNo = int.from_bytes(param[0:6],"big")
            contents = param[7:]
            file["sectors"][sectNo] = contents
        return file 
    def finish(file,param,msgs):
        file['size'] = int.from_bytes(param[0:6],'big')
        if file["expectingFile"] and len(file["sectors"])>=file['size']:
            lib.assembleFile(file["sectors"],file["name"],file['size'])
            file = {"expectingFile":False}
        else:#we are NOT finished gang
            required = [x for x in range(0,file['size']) if x not in file['sectors'].keys()]
            #for i in file['sectors'].keys():
            #    del required[i]
            for i in required:
                msgs.append(b"getPrt"+bytes(file["name"],'utf-8')+(b'\x00'*(25-len(file["name"])))+i.to_bytes(6,'big'))
        return file, msgs
    def err400(file,msgs):
        if file["expectingFile"]:
            print("400: doesn't exist / you are not authorized")
        return 
    def call(pkt,msgs,file,enc,srvPubKey):
        req = pkt[1]
        param = pkt[2]
        pktNonce = pkt[0]
        match req:
            case b"reqKey":
                msgs,enc,srvPubKey = commands.reqKey(msgs,param)    
            case b"finKey":
                msgs,enc = commands.finKey(msgs)
            case b"ready!":
                msgs = commands.ready(msgs)
            case b"sizeOf":
                msgs, file = commands.sizeOf(file,param)
            case b"partFi":
                file = commands.partFi(file,param)
            case b"finish":
                file, msgs = commands.finish(file,param,msgs)
            case b"err400":
                commands.err400(file,msgs)
            case _:
                print("invalid cmd recvd",str(req))
        return msgs,file,enc,srvPubKey
    

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
        nonce = self.nonce 
        pkt = lib.parseRawPkts([data], encrypted=encrypt, privKey=self.privKey)[0]
        
        msgs,file,skimp,srvPubKey = commands.call(pkt,msgs,file,skimp,srvPubKey)
        

        if len(msgs) != 0:
            nonce = lib.sendMessages(self,srv, msgs, encrypt=encrypt, publicKey=srvPubKey,nonce=nonce)
        else:
            if file["expectingFile"] == False:
                nonce = lib.sendMessages(self,srv, [b"ready!"], encrypt=encrypt,publicKey=srvPubKey,nonce=nonce)
            else:
                pass
        if skimp: #lazy? yeah lol
            encrypt = True
            skimp = False

        self.encrypt = encrypt
        self.skimp = skimp
        self.srvPubKey = srvPubKey
        self.file = file
        self.nonce = nonce
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