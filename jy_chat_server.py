import socket
import select

sock_list = []
BUFFER = 1024
port = 2500

# TCP 소켓
s_sock = socket.socket()
s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s_sock.bind(('10.10.21.121', port))
s_sock.listen(5)

sock_list.append(s_sock)
print(f'Waiting Connections on Port {port}...')

while True:
    r_sock, w_sock, e_sock = select.select(sock_list, [], [], 0)
    for s in r_sock:
        if s == s_sock:
            c_sock, addr = s_sock.accept()
            sock_list.append(c_sock)
            print(f'Client{addr} connected')
        else:
            try:
                data = s.recv(BUFFER)
                print(f'Received: {data.decode()}')
                if data:
                    s.send(data)

                if not data:
                    print(f'Client{addr} is offline')
                    s.close()
                    print(sock_list)
                    sock_list.remove(s)
                    continue

            except:
                print(f'Client{addr} is offline')
                s.close()
                sock_list.remove(s)
                continue

s_sock.close()
