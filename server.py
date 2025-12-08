import lib, asyncio,crypto, random

class MyDatagramProtocol(asyncio.DatagramProtocol):
#udp is for TRUE sigma males
    def __init__(self):
        self.keyChain = {}

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        print(f"Packet from {addr}")
        # ensure we use module-level keyChain
        keyChain = self.keyChain
        print(keyChain)
        try:
            if keyChain[addr[0]]["encrypt"]:
                print(keyChain[addr[0]]["encrypt"])
        except KeyError:
            keyChain[addr[0]] = {"encrypt":False, "clientPK":None}  # new ip! disable encryption

        lib.parseRawPkts([data], encrypted=keyChain[addr[0]]["encrypt"], privKey=privKey)

        param = lib.getParams(data)
        req = lib.getReq(data)
        data = None
        msgs = []

        req, param, msgs, keyChain = call(req, param, addr, msgs, keyChain)
        print(req)
        print(keyChain[addr[0]]["encrypt"])
        lib.sendMessages(self, addr, msgs,
                   encrypt=keyChain[addr[0]]["encrypt"],
                   publicKey=keyChain[addr[0]]["clientPK"] )
        self.keyChain = keyChain


def call(req, param, addr, msgs, keyChain):
    match req:
        ### key exchange ###
        case b"reqKey":
            param,msgs,keyChain = commands.reqKey(addr,param,msgs,keyChain)
        case b"finKey":
            keyChain, msgs = commands.finKey(keyChain,addr,msgs)
            keyChain[addr[0]]["encrypt"] = True
        ######
        case b"sizeOf":
            msgs = commands.sizeOf(msgs, param)
        case b"upldFi": #oh god
            commands.upldFi(param,msgs)

            pass
                
        case b"downFi": #request to download a file
            msgs = commands.downFi(param,msgs,addr)
        case b"partFi": # request for a single sector
            msgs = commands.partFi(param,msgs,addr)

        case b"stpNow":
            commands.stpNow(addr)

        case _:
            msgs = commands.other(msgs)
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
        msgs.append(b"meowtp ready!")
        return keyChain, msgs
    def sizeOf(msgs, param):
        size = lib.fileSectSize(param[-1])
        msgs.append(b"meowtp sizeOf "+{size.to_bytes(6,"big")})
        return msgs
    def downFi(param,msgs,addr):
        file = param.decode().replace("/","")
        sectorDict = lib.disassembleFile(file)
        for i in sectorDict.keys():
            #try:
            #    print(f"serving sector {i} len={len(sectorDict[i])} to {addr[0]}")
            #except Exception:
            #    print(f"serving sector {i} to {addr[0]}")
            msgs.append(b"meowtp partFi "+i.to_bytes(6, "big")+b" "+sectorDict[i])
        msgs.append(b"meowtp finish "+len(sectorDict.keys()).to_bytes(6, "big")) #TODO: send a hash?
        print("served "+file+" to "+addr[0])
        return msgs
    def partFi(param,msgs,addr):
        try:
            sectNo = int.from_bytes(param[0:6], "big")
            file = param[7:].decode().replace("/", "")
        except Exception as e:
            print("bad partFi request", e)
            return msgs

        try:
            contents = lib.readSector(file, sectNo)
            #print(f"partFi handler: sending sector {sectNo} len={len(contents)} to {addr[0]}")
            msgs.append(b"meowtp partFi "+sectNo.to_bytes(6, "big")+b" "+contents)
        except Exception as e:
            print(f"error reading sector {sectNo} of {file}: {e}")
        return msgs
    def upldFi(param,msgs):
        pass
    def stpNow(addr):
        print("client "+addr[0]+" disconnected")
        keyChain[addr[0]]["encrypt"] = False
        keyChain[addr[0]]["clientPK"] = None
        return keyChain
    def other(msgs):
        msgs.append(b"meowtp ready! ")
        return msgs




async def main():
    loop = asyncio.get_running_loop()
    print("Started UDP server")
    listen = loop.create_datagram_endpoint(lambda: MyDatagramProtocol(), local_addr=('127.0.0.1', lib.udpPort))
    transport, protocol = await listen
    try:
        await asyncio.sleep(3600) 
    finally:
        transport.close()


if __name__ == "__main__":
    privKey, pubKey, pem = crypto.createKeyPair()
    keyChain = {}
    asyncio.run(main())