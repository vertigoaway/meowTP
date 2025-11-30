import socket, sys, cryptography, lib, random # pyright: ignore[reportMissingImports]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.sendto(bytes(lib.initMsg+"\n", "utf-8"), ("127.0.0.1", lib.udpPort))
print("requesting server public key")

privKey, pubKey, pem = lib.createKeyPair()
quit = False
encrypt = False
skimp = False
srvPubKey = None
while not quit:

    received = sock.recv(4096)

    if encrypt:
        received = lib.privKeyDecrypt(received, privKey)
    try:
        received = str(received, "utf-8")
    except:
        pass
    req = lib.getReq(received)
    param = lib.getParams(received)
    msgs = []
    match req:
        case "reqKey":# we recieve server key and get requested for client key
            skimp = True
            srvPubKey = lib.recvPubkey(param)
            msgs.append("meowtp pKey "+pem.decode("utf-8"))
        case "finKey":#ensure both can read messages
            print("key exchange completed")
            msgs.append("meowtp ready ?")
        case "ready": #idle
            print(param)

        case "size": #size of a file previously requested is sent to us
            size = int(param[-1])

        case "down": #download a "sector" of file
            #TODO: file reassmbler :sob:
            print(param)
        case _:
            print("invalid request recieved D:")
    



    lib.msgHandler(msgs,srvPubKey, encrypt, sock, ("127.0.0.1",lib.udpPort))

    if skimp: #lazy? yeah lol
        encrypt = True
        skimp = False