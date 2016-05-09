import struct
import socket

# Reference: http://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data
# ------------------------------------------
"""
Helper methods to send and receive messages in sockets.
These methods will be used by both stock exchange server and client player.
"""

def send_msg(msg, client, log_f = None):
    """         
    Send message from client by prefixing with a 4-byte length to indicate the network byte order.
    :param msg: the message sent from the client
    :param client: the socket client
    :param log_f: optional log file to archive the message and client
    """
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg

    try:
        client.sendall(msg)
    except:
        print "Enable to send message. Socket may be closed"

    log_str = 'Message sent to client #{}'.format(client)

    if log_f:
        log_f.write(log_str)

    #print log_str

def recvall(n, client):
    """         
    Recieve and return a message of n bytes on the client side, return None if EOF is reached.
    :param n: size of the entire message in bytes to be received by client
    :param client: the socket client
    :return the entire message received by client, return None if EOF is reached.
    """
    # Helper function to recv n bytes or return None if EOF is hit
    data = ''
    # Keep pooling message if 
    while len(data) < n:
        packet = None
        try:
            packet = client.recv(n - len(data))
        except socket.error, e:
            pass
        if not packet:
            return None
        data += packet
    return data


def recv_msg(client):
    """         
    Receive message on the client side. We start by reading the first 4 bytes of the message and unpack
    it into an integer, which represents the length of the actual message. Then we read the actual message
    from the socket.
    :param client: the socket client
    :return the received message
    """
    # Read message length and unpack it into an integer
    raw_msglen = recvall(4, client)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(msglen, client)

    # ------------------------------------------
