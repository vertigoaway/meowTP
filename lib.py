import socket, math, asyncio
from cryptography.hazmat.primitives.asymmetric import rsa # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import serialization # pyright: ignore[reportMissingImports] QUIET!!!
from cryptography.hazmat.primitives.asymmetric import padding# pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import hashes# pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

#in this house we use reverse camel case
udpPort = 6969
keySize = 4096
maxSectorSize = int((446)-32) #cool ass magic numbers ik
#TODO: probably actually use these??

#TODO: stop being a twat and use classes
def createKeyPair(): #you are never gonna believe what this does
    privKey = rsa.generate_private_key( 
        public_exponent = 65537,
        key_size=keySize
    )
    pubKey = privKey.public_key()

    pem = pubKey.public_bytes(
        encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo)
    return privKey, pubKey, pem

def pubKeyEncrypt(msg, key):
    msg = key.encrypt(msg,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
            )
        )
    return msg

def privKeyDecrypt(msg, key):
    msg = key.decrypt(
            msg,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    return msg


def bulkEncrypt(msgs, key):
    for i, msg in enumerate(msgs):
        msgs[i] = pubKeyEncrypt(msg,key)
    return msgs

def bulkDecrypt(msgs, key):
    for i, msg in enumerate(msgs):
        msgs[i] = privKeyDecrypt(msg,key)
    return msgs


recvPubkey = lambda param: serialization.load_pem_public_key(''.join(x+'' for x in param).encode("utf-8"))

getId = lambda msg: msg[0:5]

getParams = lambda msg: msg[14:]

getReq = lambda msg: msg[7:13]


def sendMessages(sock, client_address, msgs, encrypt=False, publicKey=None):
    if encrypt:
        for i,msg in enumerate(msgs):
            msgs[i] = pubKeyEncrypt(msg,publicKey)
    
    else: #TODO: could be further optimized
        for i,msg in enumerate(msgs):
            msgs[i] = msg
    
    
    for msg in msgs:
        sock.transport.sendto(msg, client_address)
    return

def fileSectSize(fileName):
    size = math.ceil(os.path.getsize("./serving/"+fileName)/maxSectorSize)
    return size


def readSector(fileName, sector):
    size = fileSectSize(fileName)
    file = open("./serving/"+fileName,"rb")
    file.seek(0,int(maxSectorSize*sector))
    contents = file.read(maxSectorSize)
    file.close()
    return contents


#sectors is a dictionary
# {sectNo:"sectContents"}
#TODO: allow & correct missing sectors

def disassembleFile(fileName):
    sectors = {}
    fileSectorSize = fileSectSize(fileName)
    file = open("serving/"+fileName, "rb")
    for i in range(0,fileSectorSize):
        sectors[i] = file.read(maxSectorSize)
    return sectors



def assembleFile(sectors, fileName):
    fileContents = b""
    file = open("downloaded/"+fileName, "wb")
    for i in sectors.keys():
        file.write(sectors[i])
    file.write(fileContents)
    file.close()
    return
