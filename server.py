"""Experiment with sockets in py."""
# imports
import socket    # for connections
import threading # to serve multiple clients ata  time
import signal    # to close server properly
import sys       # for sys.exit()
import json      # to serialize data
import re        # Regular expressions for pattern matching

# Constents
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
# Size limit of header(data size sent beforehand)
HEADER = 64     
# encoding style
FORMAT = 'utf-8'

# Special codes that have meaning tos erver and client
DISCONNECT = "<<!DISCONNECT<<"
NAME_ERROR = '<<!NAMEERROR<<'
RECV_ERROR = '<<!RECVERROR<<'
ACK = "<<!ACK<<"


# create a socket
try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    server.bind(ADDR)
except:
    print("Failed to create socket")
    sys.exit()

# dictionary to store clients
clients = {}

def handler_interupt(sig_recv, frame):
    '''Handles being killed'''
    print("Disconnecting clients")
    # close all sockets
    for client in clients.values():
        client.close()
    print("Server shutdown")
    server.close()
    sys.exit()


def send_message(client, msg):
    """Send message to server.
    
    Steps:
    - send message length
    - send message
    - encode message and message length before sending
    """
    message = str(msg).encode(FORMAT)
    msg_len = len(message)
    send_len = str(msg_len).encode(FORMAT)
    # pade the length and make it as long as HEADER
    send_len += b" " * (HEADER - len(send_len))
    try:
        client.send(send_len)
        client.send(message)
    except:
        print("Failed to daliver message")


# Handles whom to deliver the message
def broadcast(msg:dict):
    """Broadcast message to everyone"""
    # Check if the message is suppose to go to a specific person
    # Or to everyone
    if msg['to'] == 'all':
        for name, client in clients.items():
            # Don't send the message back to the sender
            if name != msg['from']:
                send_message(client, json.dumps(msg))
    else:
        if msg['to'] in clients:
            send_message(clients[msg['to']], json.dumps(msg))

def recv(client):
    '''receives message from client
        
    steps:
    - receive length
    - receive message based on length
    - decode and return the message
    Error code:
    - in case msg_len is not found return RECV_ERROR
    '''
    try:
        msg_len = client.recv(HEADER).decode(FORMAT)
    except:
        print("Falied to get message length")
    else:
        if msg_len:
            try:
                msg_len = int(msg_len)
                msg = client.recv(msg_len).decode(FORMAT)
            except ValueError:
                print("Invalid message length")
            except:
                print("Failed to receive message")
            else:
                return msg
    return RECV_ERROR

def authonticate(client, addr):
    '''varify if user can join chat
    Steps:
    - getusername
    - check if username is already being used
    - create a separate thread and handle the client there
    '''
    # User is suppose to send username as it tries to connect
    msg = recv(client)
    if not re.match('^/set-name .+', msg):
        # Invalied input close connection
        send_message(client, NAME_ERROR)
        client.close()
        return None
    uname = msg[len('/set-name '):]
    if uname in clients:
        # Cann't have duplicate names close connection
        send_message(client, NAME_ERROR)
        print(f"Falied login attempt of {uname}:{addr}")
        client.close()
    else:
        # Username accepted Confirm connection
        send_message(client, ACK)
        # add client to clients dictionary
        clients[uname] = client
        # start a new thread to handle client
        thread = threading.Thread(target=handle_client, args=(uname,client, addr))
        # make the thread die with the main program
        thread.daemon = True
        thread.start()
        print(f"[ACTIVE THREADS] : {threading.active_count() - 2}")

def handle_client(uname, conn, addr):
    """Handles client.
    
    Step:
    - receive message from client and forword it
    """
    print(f"[NEW CONNECTION] {uname}@{addr} connected")

    connected = True
    while connected:
            msg = recv(conn)
            if msg == DISCONNECT or msg == RECV_ERROR:
                # Remove client
                print("[DISCONNECT] "+str(addr)+" disconnected")
                del clients[uname]
                connected = False
                break
            # forword the message
            broadcast(json.loads(msg))
    conn.close()

def start():
    """Start the server."""

    # Listen for connections
    server.listen()
    print("[RUNNING] server is running on "+str(SERVER)+":"+str(PORT))
    
    while True:
        # Accept connections and create a new thread to handle
        # aunthontication
        conn, addr = server.accept()
        thread = threading.Thread(target=authonticate, args=(conn, addr))
        thread.daemon = True
        thread.start()


if __name__ == '__main__':
    # set SIGINT handler
    signal.signal(signal.SIGINT, handler_interupt)
    print("[STARTING] server is starting...")
    start()
