from cryptography.hazmat.primitives.asymmetric import rsa # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import serialization # pyright: ignore[reportMissingImports] QUIET!!!
from cryptography.hazmat.primitives.asymmetric import padding# pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives import hashes# pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import threading
keySize = 4096


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

def pubKeyEncrypt(msg, key, nonce): #single threaded encrypt
    print(msg)
    msg = key.encrypt(msg+nonce.tobytes(6),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
            )
        )
    return msg

def privKeyDecrypt(msg, key):#single threaded decrypt
    msg = key.decrypt(
            msg,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    return msg


def bulkEncrypt(msgs, key, nonce): #MT encryption
    threads = []
    for i, msg in enumerate(msgs):
        thread = threading.Thread(pubKeyEncrypt, args=[msg,key,nonce])
        threads.append(thread)
        nonce+=1
        thread.start()
    for i,t in enumerate(threads):
        msgs[i] = t.join()
    return msgs

def bulkDecrypt(msgs, key):#MT decryption
    threads = []
    for i, msg in enumerate(msgs):
        thread = threading.Thread(privKeyDecrypt, args=[msg,key])
        threads.append(thread)
        thread.start()
    for i,t in enumerate(threads):
        msgs[i] = t.join()
    return msgs


recvPubkey = lambda param: serialization.load_pem_public_key(''.join(x+'' for x in param).encode("utf-8"))