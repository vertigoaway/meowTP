import socket, sys, cryptography, lib, random # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives.asymmetric import rsa # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import serialization # pyright: ignore[reportMissingImports] QUIET!!!
from cryptography.hazmat.primitives.asymmetric import padding# pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import hashes# pyright: ignore[reportMissingImports]
#client! 
#will probably be coded as procedurally oriented for now, i wanna get a working prototype
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.sendto(bytes(lib.initMsg+"\n", "utf-8"), ("127.0.0.1", lib.udpPort))
print("requesting server public key")

privKey, pubKey, pem = lib.createKeyPair()
quit = False
encrypt = False
skimp = False
while not quit:

    received = sock.recv(1024)

    if encrypt:
        received = lib.privKeyDecrypt(received, privKey)
    else:
        received = str(received, "utf-8")
    tmp, req, param = received.split(" ", 2)
    if tmp!= "meowtp" and not encrypt:
        raise ConnectionError('server not meowtp')

    match req:
        case "hand":
            skimp = True
            srvPubKey = serialization.load_pem_public_key(param.encode("utf-8"))
            print("server public key acquired")
            msg = bytes("meowtp shake? "+pem.decode("utf-8"),"utf-8")
            print("sending our public key")
        case "shake":
            print("server acquired our public key")
            print("key exchange completed")
            msg = "meowtp meow meow meow meow"
        case "null":
            print("req we sent was outside the bounds of servers commands :(")
            exit()
    if encrypt:
        msg = lib.pubKeyEncrypt(bytes(msg,"utf-8"),srvPubKey)

    if skimp: #sshhhhh me when im lazy
        encrypt = True
        skimp = False
    sock.sendto(msg,("127.0.0.1",lib.udpPort))
