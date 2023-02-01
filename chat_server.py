import socket
import select


class MainServer:
    def __init__(self):
        self.sock_list = []
        self.BUFFER = 1024
        self.ip = '10.10.21.121'
        self.port = 9000
        self.s_sock = socket.socket()

        self.initialize_socket()
        self.receive_message()

    def initialize_socket(self):
        self.s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s_sock.bind((self.ip, self.port))
        self.s_sock.listen()

        self.sock_list.append(self.s_sock)
        print(f'Waiting Connections on Port {self.port}...')

    def receive_message(self):
        while True:
            r_sock, w_sock, e_sock = select.select(self.sock_list, [], [], 0)
            for s in r_sock:

                if s == self.s_sock:
                    c_sock, addr = self.s_sock.accept()
                    self.sock_list.append(c_sock)
                    print(f'Client{addr} connected')

                else:
                    try:
                        data = s.recv(self.BUFFER).decode()
                        print(f'Received: {s.getpeername()}: {data}')

                        if data:
                            s.send(data.encode())
                            msg = eval(data)
                            print(msg)
                            print(type(msg))

                        if not data:
                            print(f'Client{s.getpeername()} is offline')
                            s.close()
                            self.sock_list.remove(s)
                            continue

                    except ConnectionResetError:
                        print(f'Client{s.getpeername()} is offline')
                        s.close()
                        self.sock_list.remove(s)
                        continue
