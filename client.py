import socket, lib, crypto, asyncio # pyright: ignore[reportMissingImports]
import threading
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536*8) #bigga buffa, prob doesnt matter cause of async

srv = ("127.0.0.1",lib.udpPort)


def interface(msgs):
    print("enter a request!")
    print("Download:")
    print('\t downFi <filename>')
    print("Upload:")
    print('\t upldFi <filename>')
    print("Quit:")
    print("\t quit")
    cmd = "meowtp "+input("meowtp:")
    req = lib.getReq(cmd)
    param = lib.getParams(cmd)
    match req:
        case "downFi":
            cmd = cmd.replace("/","")
            msgs.append(cmd.encode())
            file = {"expectingFile":True,"name":cmd[14:],"sectors":{}}
        case "upldFi":
            cmd = cmd.replace("/","")
            msgs.append(cmd.encode())
            file = {"sendingFile":True,"name":cmd[14:],"sectors":lib.disassembleFile(cmd[14:])} 
            #TODO: finish upload implementation
        case "quit":
            global quit
            quit = True
            msgs.append(b"meowtp stpNow")
            file = {"expectingFile":False}
        case _:
            print("err")
            raise Exception("invalid command"+cmd)
        
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
    def connection_made(self, transport):
        self.transport = transport
        print('connection established')
        transport.sendto(bytes("meowtp reqKey ", "utf-8")+self.pem, (srv))
    def datagram_received(self, data, addr):
        encrypt = self.encrypt 
        skimp = self.skimp 
        srvPubKey = self.srvPubKey
        file = self.file 
        msgs = self.msgs 
        req,param = lib.parseRawPkts([data], encrypted=encrypt, privKey=self.privKey)[0]
        match req:
            ### key exchange ###
            case b"reqKey":# we recieve server key and get requested for client key
                skimp = True
                srvPubKey = crypto.recvPubkey(param)
                msgs.append(b"meowtp finKey ")
            case b"finKey":#ensure both can read messages
                print("key exchange completed")
                msgs.append(b"meowtp finKey")
            case b"ready!": #idle
                msgs,file = interface(msgs)


            case b"partFi": #download a "sector" of file
                if file["expectingFile"]:
                    sectNo = int.from_bytes(param[0:6],"big")
                    contents = param[7:]
                    file["sectors"][sectNo] = contents
                    #print(f"received sector {sectNo} len={len(contents)}")
                    if "missing" in file: #missing sectors D:
                        try:
                            before = len(file["missing"])
                            file["missing"].discard(sectNo)
                            after = len(file["missing"])
                            if after != before:
                                print(f"removed sector {sectNo} from missing (remaining {after})")
                                expected = file.get("expected") 
                                if expected is not None and len(file["sectors"]) >= expected: #yahoo!
                                    try:
                                        print("all missing sectors received — assembling file")
                                        lib.assembleFile(file["sectors"], file["name"])
                                    except Exception as e:
                                        print("error assembling file:", e)
                                    file = {"expectingFile":False}
                        except Exception:
                            file["missing"] = set(file.get("missing", set()))
                            file["missing"].discard(sectNo)
                            print(f"removed sector {sectNo} from missing (set recreated)")
                    if "retries" in file:
                        file["retries"] = 0
            case b"finish":
                if file["expectingFile"]:
                    expected = int.from_bytes(param[0:6], "big")
                    got = len(file["sectors"])
                    # store expected count for later checks
                    file["expected"] = expected
                    if got >= expected:
                        # all sectors received
                        lib.assembleFile(file["sectors"], file["name"])
                        file = {"expectingFile":False}
                    else:
                        # detect missing sectors and request them
                        missing = [i for i in range(expected) if i not in file["sectors"]]
                        print(f"finish received: expected {expected}, got {got}, missing {len(missing)} sectors")
                        # store missing set and retry metadata
                        file.setdefault("missing", set()).update(missing)
                        file.setdefault("retries", 0)
                        # send requests for missing sectors
                        self._send_missing_requests()
                        # schedule a check after a short delay to retry if still missing
                        try:
                            loop = asyncio.get_running_loop()
                            loop.call_later(1.0, lambda: asyncio.create_task(self._check_missing()))
                        except Exception:
                            # fallback: use threading timer if no running loop
                            threading.Timer(1.0, lambda: asyncio.run(self._check_missing())).start()
            case b"err400": #exception
                if file["expectingFile"]:
                    print("400: doesn't exist / you are not authorized")
                    file["expectingFile"] = {"expectingFile":False}
                    interface(msgs)

            case _:
                print("invalid request recieved D:")
                print(req)
        


        if len(msgs) != 0:
            lib.sendMessages(self,srv, msgs, encrypt=encrypt, publicKey=srvPubKey)
        else:
            if file["expectingFile"] == False:
                lib.sendMessages(self,srv, [b"meowtp ready!"], encrypt=encrypt,publicKey=srvPubKey)
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

    async def _check_missing(self):
        """Check for missing sectors, resend requests up to a retry limit, and assemble when complete."""
        MAX_RETRIES = 5
        RETRY_DELAY = 1.0
        file = self.file
        if not file.get("expectingFile"):
            return

        missing = sorted(list(file.get("missing", set())))
        if not missing:
            # nothing missing, try assemble
            try:
                # expected can be stored from finish
                expected = file.get("expected")
                # only assemble if we have enough sectors
                if expected is None or len(file["sectors"]) >= expected:
                    lib.assembleFile(file["sectors"], file["name"])
                self.file = {"expectingFile":False}
            except Exception:
                pass
            return

        retries = file.get("retries", 0)
        if retries >= MAX_RETRIES:
            print(f"Failed to retrieve {len(missing)} sectors after {retries} retries: {missing}")
            return

        # resend requests for missing sectors
        file["retries"] = retries + 1
        print(f"Retrying missing sectors (attempt {file['retries']}/{MAX_RETRIES}): {missing}")
        self._send_missing_requests()
        # schedule next check
        loop = asyncio.get_running_loop()
        loop.call_later(RETRY_DELAY, lambda: asyncio.create_task(self._check_missing()))

    def _send_missing_requests(self):
        """Send partFi requests to the server for each missing sector."""
        file = self.file
        if not file.get("expectingFile"):
            return
        missing = sorted(list(file.get("missing", set())))
        if not missing:
            return

        msgs = []
        print(f"_send_missing_requests: preparing {len(missing)} requests for missing sectors: {missing}")
        for sectNo in missing:
            # request format: "meowtp partFi <6byte sectNo> <filename>"
            msgs.append(bytes("meowtp partFi ", "utf-8") + sectNo.to_bytes(6, "big") + b" " + file["name"].encode())

        # send messages immediately
        try:
            print(f"_send_missing_requests: sending {len(msgs)} messages")
            lib.sendMessages(self, srv, msgs, encrypt=self.encrypt, publicKey=self.srvPubKey)
            msgs = []
        except Exception as e:
            print("error sending missing-sector requests:", e)



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