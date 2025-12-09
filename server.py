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
            keyChain[addr[0]] = {"encrypt":False, "clientPK":None}  # new ip! disable encryption

        req,param = lib.parseRawPkts([data], encrypted=keyChain[addr[0]]["encrypt"], privKey=privKey)[0]
        data = None

        msgs = []
        print(f"Packet from {addr}: {req}")
        # call the handler correctly
        req, param, msgs, keyChain = call(req, param, addr, msgs, keyChain)

        lib.sendMessages(self, addr, msgs,
                   encrypt=keyChain[addr[0]]["encrypt"],
                   publicKey=keyChain[addr[0]]["clientPK"] )



def call(req, param, addr, msgs, keyChain):
    match req:
        ### key exchange ###
        case b"reqKey":
            param,msgs,keyChain = commands.reqKey(addr,param,msgs,keyChain)

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

        case _:
            msgs = commands.other(msgs,req)
    return req, param, msgs, keyChain


class commands:
    def reqKey(addr,param,msgs,keyChain):
        keyChain[addr[0]] = {
                        "clientPK":crypto.recvPubkey(param),
                        "encrypt":False}
        msgs.append(b"meowtp reqKey "+pem)
        return param,msgs,keyChain
    def finKey(keyChain,addr,msgs):
        keyChain[addr[0]]["encrypt"] = True
        msgs.append(b"meowtp ready! ")
        return keyChain, msgs
    def sizeOf(msgs, param):
        size = lib.fileSectSize(param[-1])
        msgs.append(b"meowtp sizeOf "+{size.to_bytes(6,"big")})
        return msgs
    def downFi(param,msgs,addr):
        file = param.decode().replace("/","")
        sectorDict = lib.disassembleFile(file)
        for i in sectorDict.keys():
            msgs.append(b"meowtp partFi "+i.to_bytes(6, "big")+b" "+sectorDict[i])
        msgs.append(b"meowtp finish "+len(sectorDict.keys()).to_bytes(6, "big")) #TODO: send a hash?
        print("served "+file+" to "+addr[0])
        return msgs
    
    def upldFi(param,msgs):
        pass

    def stpNow(addr):
        print("client "+addr[0]+" disconnected")
        keyChain[addr[0]]["encrypt"] = False
        keyChain[addr[0]]["clientPK"] = None
        return keyChain
    
    def other(msgs, req):
        print("unknown cmd: "+str(req))
        msgs.append(b"meowtp ready! ")
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
