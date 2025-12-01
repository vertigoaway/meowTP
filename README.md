MeowTP!!!

blind practice project for networking. dont expect this to work well
if i can get it to send and recieve a file ill be happy

default port is 6969

handshake steps:
1. client sends "reqKey"
2. server sends "reqKey" and attaches server public key
3. client sends "sndKey" and attaches client public key
4. server sends "finKey" encrypted as a confirmation 



objectives
  - ✅ RSA diffie helman key exchange
  - ✅ all messages are encrypted after handshake
  - ✅ very few security flaws in encryption implementation 
  - 🟨 server can handle multiple clients
  - ✅ client and server can send packets in bulk
  - 🟨🔨 client and server can recieve packets in bulk
  - ✅ client can download files from server
    - ? download <= 0.5MB with little/no corruption
    - ? download <= 1MB with little/no corruption
    - ? download <= 10MB with little/no corruption
    - ? download <= 1GB with little/no corruption
  - 🔨 client can upload files to server
  - 🟨🔨 client has rudimentary cli interface
  - 🔨 actually use OOP
  - 🔨 perhaps make decent code
  - ❌ remove as much packet bloat as possilbe
  - ❌ refactor server to use async
  - ❌ refactor client to use async
  - ❌ use bytes instead of strings
  - ❌ detect and correct packet loss
  - ❌ compress files
  - ❌ negotiate packet size
  - ❌ add ED25519
  - ❌ add quantum proof algorithms
  - ❌ add user authentication
  - ❌ persistent keys (?)
  - ❌ annotate code
  - ❌ prettyify code :3
  - ❌ document functions
  - ❌ split lib into more files
  - ❌ add classes to lib