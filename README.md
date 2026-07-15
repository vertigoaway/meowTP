# MeowTP

### Meow Transfer Protocol

> *A lightweight binary application protocol for structured message exchange over TCP.*

MeowTP is an experimental protocol written in Python that focuses on simplicity, efficiency, and extensibility. It uses MessagePack for serialization, optional Zstandard compression, and a small framed binary protocol designed to be easy to implement in other languages.

The project is currently a work in progress and serves as both a networking library and a testbed for protocol design.

---

## Features

* Binary framed protocol
* MessagePack serialization
* Optional Zstandard compression
* Persistent TCP connections
* Thread-safe server implementation
* Extensible protocol flags
* Language-agnostic wire format
* Minimal protocol overhead

---

## Frame Format

Every packet is transmitted as a single frame.

```
+------------+------------+----------------------+
| Length     | Flags      | Payload              |
| 4 bytes    | 1 byte     | Variable             |
+------------+------------+----------------------+
```

### Length

Unsigned 32-bit big-endian integer representing the payload size.

Maximum length value defined by MAX_FRAME in netlib.py

### Flags

Each bit represents protocol features.

| Bit | Meaning                         | Status      |
| --: | ------------------------------- | ----------- |
|   0 | Payload is Zstandard compressed | Implemented |
|   1 | Reserved                        | Unused      |
|   2 | Reserved                        | Unused      |
|   3 | Reserved                        | Unused      |
|   4 | Reserved                        | Unused      |
|   5 | Reserved                        | Unused      |
|   6 | Reserved                        | Unused      |
|   7 | Reserved                        | Unused      |

Future protocol revisions may use additional bits for features such as encryption.

---

## Serialization

Objects are serialized using MessagePack.

Small packets are transmitted uncompressed.

Larger packets are automatically compressed using Zstandard to reduce bandwidth usage.

---

## Request Format

Requests follow the general form:

```python
{
    "cmd": "<command>",
    "<command>": {
        ...
    }
}
```

Example:

```python
{
    "cmd": "query",
    "query": {
        "k": "apple"
    }
}
```

---

## Responses

Responses currently return status codes and any associated data.

Example:

```python
{
    "status": 200,
    "result": {
        "k": "apple",
        "v": 1648
    }
}
```

---

## Implemented Commands

### Query

Retrieve an object by key ~~or value~~.

---

### Post

Insert a new key/value pair.

Fails if the key already exists.

---

### Push

Insert or overwrite a key/value pair.



---

## Example

```python
client.post("username", "verti")

response = client.query("username")

print(response)
```

Result:

```python
{
    "status": 200,
    "result": {
        "k": "username",
        "v": "verti"
    }
}
```

---

## Dependencies

* Python 3.13+
* msgpack

## Disclaimer

MeowTP is an experimental protocol intended for learning, experimentation, and future development. The wire format and API may change as the project evolves.