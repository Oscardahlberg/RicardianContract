import socket
import jpysocket

PORT = 49000


def post(msg):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), PORT))
    s.send(jpysocket.jpyencode(msg))
    s.close()


def get(msg):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), PORT))
    s.send(jpysocket.jpyencode(msg))

    msg = s.recv(1024)
    msg = jpysocket.jpydecode(msg)
    print("Received: ", msg)
    s.close()
