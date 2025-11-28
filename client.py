import socket
import sys
import lib

# SOCK_DGRAM is the socket type to use for UDP sockets
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# As you can see, there is no connect() call; UDP has no connections.
# Instead, data is directly sent to the recipient via sendto().
sock.sendto(bytes(lib.initMsg + "\n", "utf-8"), ("127.0.0.1", lib.udpPort))
received = str(sock.recv(1024), "utf-8")

print("sent:    ", lib.initMsg)

if received == lib.greetMsg:
    print("server alive!")
else:
    raise ConnectionError("server sent: \""+received+"\"\n Invalid response.")