import socket
import select


class MainServer:
    sock_list = []
    BUFFER = 1024
    port = 9000

    s_sock = socket.socket()
    s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s_sock.bind(('10.10.21.121', port))
    s_sock.listen()

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
                    data = s.recv(BUFFER).decode()
                    print(f'Received: {s.getpeername()}: {data}')

                    if data:
                        s.send(data.encode())
                        msg = eval(data)
                        print(msg)
                        print(type(msg))

                    if not data:
                        print(f'Client{s.getpeername()} is offline')
                        s.close()
                        sock_list.remove(s)
                        continue

                except ConnectionResetError:
                    print(f'Client{s.getpeername()} is offline')
                    s.close()
                    sock_list.remove(s)
                    continue
