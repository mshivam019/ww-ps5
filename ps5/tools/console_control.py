"""Minimal FTX2 control client for the local PS5Upload service."""
import json
import os
import socket
import struct

HOST = os.environ.get("PS5_HOST", "127.0.0.1")
PORT = int(os.environ.get("PS5_CONTROL_PORT", "9114"))
HEADER = struct.Struct("<IHHIQQ")
MAGIC = int.from_bytes(b"FTX2", "little")


def _receive(connection, length):
    result = bytearray()
    while len(result) < length:
        chunk = connection.recv(length - len(result))
        if not chunk:
            raise ConnectionError("PS5 control connection closed before the response completed")
        result.extend(chunk)
    return bytes(result)


def call(kind, args):
    payload = json.dumps(args).encode()
    with socket.create_connection((HOST, PORT), timeout=60) as connection:
        connection.sendall(HEADER.pack(MAGIC, 1, kind, 0, len(payload), 1) + payload)
        magic, version, response, _, length, trace = HEADER.unpack(_receive(connection, HEADER.size))
        if magic != MAGIC or version != 1 or trace != 1 or length > 16 * 1024 * 1024:
            raise RuntimeError("Invalid PS5 control response header")
        body = _receive(connection, length)
    if response == 3:
        raise RuntimeError(body.decode(errors="replace"))
    return body
