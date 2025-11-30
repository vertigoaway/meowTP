import socket, sys, cryptography, lib, random # pyright: ignore[reportMissingImports]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.sendto(bytes(lib.initMsg+"\n", "utf-8"), ("127.0.0.1", lib.udpPort))
print("requesting server public key")

privKey, pubKey, pem = lib.createKeyPair()
quit = False
encrypt = False
skimp = False
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
    
    match req:
        case "hand":# keyexch pt 1
            skimp = True
            srvPubKey = lib.recvPubkey(param)
            msg = bytes("meowtp shake? "+pem.decode("utf-8"),"utf-8")
        case "shake":#keyexch pt 2
            print("key exchange completed")
            msg = "meowtp meow ?"
        case "await": #sent when server is waiting for new request
            print(param)
        case "down":
            #TODO: file reassmbler :sob:
            print(param)
        case _:
            print("request param invalid D:")
    
    if encrypt:
        msg = lib.pubKeyEncrypt(bytes(msg,"utf-8"),srvPubKey)

    if skimp: #sshhhhh me when im lazy
        encrypt = True
        skimp = False
    sock.sendto(msg,("127.0.0.1",lib.udpPort))

