"""Client to test the server."""
import socket
import sys
import threading
import signal
# import time
import json
import re

# Constents
PORT = 5050
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT = "<<!DISCONNECT<<"
NAME_ERROR = '<<!NAMEERROR<<'
RECV_ERROR = '<<!RECVERROR<<'
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)
ACK = "<<!ACK<<"

def interupt_handler(sig_recv, frame):
    send(DISCONNECT)
    client.close()
    # print("Closed")
    # threads['recv'].join()
    # threads['send'].join()
    # sys.exit()

# Setup socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# connect to server
try:
    print("Connecting to server")
    client.connect(ADDR)
except ConnectionRefusedError:
    print("Connection Error!!")
    sys.exit()
else:
    print("Connected to "+SERVER+":"+str(PORT))

def send(msg:str):
    """Send message to server."""
    message = msg.encode(FORMAT)
    msg_len = len(message)
    send_len = str(msg_len).encode(FORMAT)
    send_len += b' ' * (HEADER - len(send_len))
    client.send(send_len)
    client.send(message)

def recv():
    '''receives message from server'''
    msg_len = client.recv(HEADER).decode(FORMAT)
    if msg_len:
        msg_len = int(msg_len)
        msg = client.recv(msg_len).decode(FORMAT)
        return msg
    return RECV_ERROR

def handle_cmd(msg:str):
    if re.match('/set-to .*',msg):
        global to 
        to = msg[len('/set-to '):]

threads = {}

def thread_receive():
    '''The thread to listen to server'''
    while True:
        msg = recv()
        if msg == RECV_ERROR:
            print("Connection closed")
            # client.close()
            sys.exit()
        # print(f"DEBUG: received {msg}")
        massage = json.loads(msg)
        print('\n\t\t'+massage['msg'], end="\n")
        if 'from' in massage:
            print(f"\t  From: {massage['from']}")
        print("Msg: ", end="")
        sys.stdout.flush()
        

def thread_send():
    '''thread to listen to user'''
    msg_in = input("Msg: ")
    while msg_in:
        if re.match('/.*',msg_in):
            handle_cmd(msg_in)
        else:
            msg = {
                "from": user,
                "to": to,
                "msg":msg_in
                }
            msg = json.dumps(msg)
            # print(f"DEBUG: sending {msg}")
            send(msg)
        msg_in = input("Msg: ")
    # Close connection
    send(DISCONNECT)
    client.close()
    sys.exit()
    


def start():
    global user
    user = input("Username: ")
    global to
    to = 'all'
    send(f"/set-name {user}")
    ret = recv()
    if ret == NAME_ERROR:
        print("NAME_ERROR occured username already taken or banned")
        client.close()
        sys.exit(0)

    threads['recv'] = threading.Thread(target=thread_receive)
    threads['send'] = threading.Thread(target=thread_send)
    threads['send'].daemon = True
    threads['recv'].start()
    threads['send'].start()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, interupt_handler)
    start()
