import socket
from cryptography.hazmat.primitives.asymmetric import rsa # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import serialization # pyright: ignore[reportMissingImports] QUIET!!!
from cryptography.hazmat.primitives.asymmetric import padding# pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import hashes# pyright: ignore[reportMissingImports]
#in this house we use reverse camel case
udpPort = 6969

initMsg = "meowtp hand? ?"
greetMsg = "meowtp pk"# + pubkey

#yeah this is gonna get used more soon
def createKeyPair():
    privKey = rsa.generate_private_key( #everytime program is started, a new key is used :3
        public_exponent = 65537,
        key_size=4096
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
    msg = msg.decode("utf-8")
    return msg