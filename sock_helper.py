import struct
import socket

# Reference: http://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data
# ------------------------------------------

def send_msg(msg, client, log_f = None):
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
    # Helper function to recv n bytes or return None if EOF is hit
    data = ''
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
    # Read message length and unpack it into an integer
    raw_msglen = recvall(4, client)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(msglen, client)

    # ------------------------------------------