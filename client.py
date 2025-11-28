import socket, sys, cryptography, lib, random # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives.asymmetric import rsa # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import serialization # pyright: ignore[reportMissingImports] QUIET!!!


#client! 
#will probably be coded as procedurally oriented for now, i wanna get a working prototype
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


sock.sendto(bytes(lib.initMsg + "\n", "utf-8"), ("127.0.0.1", lib.udpPort))
received = str(sock.recv(1024), "utf-8")

print("sent:    ", lib.initMsg)

tmp, snt, param = received.split(" ", 2)

if tmp!= "meowtp":
    raise ConnectionError('server not meowtp')

