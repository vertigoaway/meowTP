import lib, asyncio,crypto # pyright: ignore[reportMissingImports]


class MyDatagramProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):

        # ensure we use module-level keyChain
        global keyChain, privKey
        if 'keyChain' not in globals():
            keyChain = {}

        try:
            if keyChain[addr[0]]["encrypt"]:
                pass
        except KeyError:
            keyChain[addr[0]] = {"encrypt":False, "clientPK":None, "nonce":1}  # new ip! disable encryption

        pktNonce,req,param = lib.parseRawPkts([data], encrypted=keyChain[addr[0]]["encrypt"], privKey=privKey)[0]
        data = None

        msgs = []
        print(f"Packet from {addr} {pktNonce}:{req}")
        # call the handler correctly
        msgs, keyChain = call(req, param, addr, msgs, keyChain)

        tmp = lib.sendMessages(self, addr, msgs,
                   encrypt=keyChain[addr[0]]["encrypt"],
                   publicKey=keyChain[addr[0]]["clientPK"],nonce=keyChain[addr[0]]["nonce"])
        keyChain[addr[0]]["nonce"] = tmp


def call(req, param, addr, msgs, keyChain):
    match req:
        ### key exchange ###
        case b"reqKey":
            msgs,keyChain = commands.reqKey(addr,param,msgs,keyChain)

        case b"finKey":
            keyChain, msgs = commands.finKey(keyChain,addr,msgs)
        ######
        case b"sizeOf":
            msgs = commands.sizeOf(msgs, param)
        case b"upldFi": #fi contents
            commands.upldFi(param,msgs)

            pass
                
        case b"downFi": #fi
            msgs = commands.downFi(param,msgs,addr)

        case b"stpNow":
            commands.stpNow(addr)
        case b"getPrt":
            msgs = commands.getPrt(msgs,param)

        case _:
            msgs = commands.other(msgs,req)
    return msgs, keyChain


class commands:
    def reqKey(addr,param,msgs,keyChain):#recieve then send pubkeys
        keyChain[addr[0]] = {
                        "clientPK":crypto.recvPubkey(param),
                        "encrypt":False,
                        "nonce":1}
        msgs.append(b"reqKey"+pem)
        return msgs,keyChain
    def finKey(keyChain,addr,msgs):#begin encrypting
        keyChain[addr[0]]["encrypt"] = True
        msgs.append(b"ready!")
        return keyChain, msgs
    def getPrt(msgs, param):#get one part of a file
        file = param[0:25].decode().replace("..","").strip().replace('\x00','')
        partNo = int.from_bytes(param[25:],'big')
        sector = lib.readSector(fileName=file,sector=partNo)
        msgs.append(b"partFi"+partNo.to_bytes(6,'big')+b" "+sector)
        return msgs
    def sizeOf(msgs, param):#get size of file
        size = lib.fileSectSize(param.decode('utf-8'))
        msgs.append(b"sizeOf"+size.to_bytes(6,"big"))
        return msgs
    def downFi(param,msgs,addr):#get all parts of a file
        file = param.decode().replace("/","")
        sectorDict = lib.disassembleFile(file)
        for i in sectorDict.keys():
            msgs.append(b"partFi"+i.to_bytes(6, "big")+b" "+sectorDict[i])
        msgs.append(b"finish"+len(sectorDict.keys()).to_bytes(6, "big")) #TODO: send a hash?
        print("served "+file+" to "+addr[0])
        return msgs
    
    def upldFi(param,msgs):#begin recieving a file upload
        pass

    def stpNow(addr):#stop and reset connection
        print("client "+addr[0]+" disconnected")
        keyChain[addr[0]]["encrypt"] = False
        keyChain[addr[0]]["clientPK"] = None
        return keyChain
    
    def other(msgs, req): #unknown req recieved
        print("unknown cmd: "+str(req))
        msgs.append(b"ready!")
        return msgs




async def main():
    loop = asyncio.get_running_loop()
    print("Started UDP server")
    # Create a UDP server
    listen = loop.create_datagram_endpoint(lambda: MyDatagramProtocol(), local_addr=('127.0.0.1', lib.udpPort))
    transport, protocol = await listen
    try:
        await asyncio.sleep(3600)  # Run for 1 hour
    finally:
        transport.close()


if __name__ == "__main__":
    privKey, pubKey, pem = crypto.createKeyPair()
    keyChain = {}
    asyncio.run(main())
