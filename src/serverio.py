import socket


def recv(ip:str, port:int, cmd:str) -> str:
    conn = __connect(ip, port)
    __send(conn, cmd.encode('utf-8'))
    data = __recv(conn)
    __close(conn)
    return data

def send(ip:str, port:int, cmd:str, data=b''):
    conn = __connect(ip, port)
    __send(conn, cmd.encode('utf-8'))
    if data:
        __send(conn, data)
    __close(conn)


#-----------
# Low level 
#-----------

def __connect(ip:str, port:int):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((ip, port))
    return conn

def __close(conn:socket):
    conn.shutdown(1)
    conn.close()

def __read_size(conn:socket):
    b_size = conn.recv(4)
    return int.from_bytes(b_size, byteorder='big')

def __read_data(conn:socket, size:int):
    chunks = []
    bytes_recved = 0
    while bytes_recved < size:
        chunk = conn.recv(size - bytes_recved)
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        chunks.append(chunk)
        bytes_recved += len(chunk)
    return b''.join(chunks)

def __recv(conn:socket.socket) -> str:
    size = __read_size(conn)
    data = __read_data(conn, size)
    return data.decode('utf-8')

def __send(conn:socket.socket, data=bytes):
    size = len(data)
    conn.send(size.to_bytes(4, byteorder='big'))
    conn.send(data)

    