import json

import pymysql
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
                    self.set_client_default(c_sock, addr[0])

                else:
                    try:
                        data = s.recv(self.BUFFER).decode()
                        print(f'Received: {s.getpeername()}: {data}')

                        if data:
                            message = eval(data)
                            self.command_processor(s.getpeername()[0], message, s)
                            s.send(data.encode())

                        if not data:
                            self.connection_lost(s)
                            continue

                    except ConnectionResetError:
                        self.connection_lost(s)
                        continue

    def connection_lost(self, s):
        print(f'Client{s.getpeername()} is offline')
        s.close()
        self.sock_list.remove(s)

    def command_processor(self, user_ip, message, s):
        print(f'메시지: {message}')
        print(type(message))
        command = message[0]
        content = message[1]
        if command == '/set_nickname':
            self.set_client_nickname(user_ip, content, s)

    def set_client_default(self, c_sock, ip):
        self.set_user_status_login(ip)
        self.set_client_nickname_label(c_sock, ip)

    def set_user_status_login(self, ip):
        sql = f'UPDATE state SET port=9000 WHERE ip="{ip}"'
        self.execute_db(sql)

    def set_user_status_logout(self, ip):
        sql = f'UPDATE state SET port=0 WHERE ip="{ip}"'
        self.execute_db(sql)

    def set_client_nickname_label(self, c_sock, ip):
        sql = f'SELECT 닉네임 FROM state WHERE ip="{ip}"'
        nickname = self.execute_db(sql)[0][0]
        # print(nickname)
        # print(f'client_ip: {ip}')
        msg = ['/set_nickname_label', nickname]
        data = json.dumps(msg)
        c_sock.send(data.encode())

    def set_client_nickname(self, user_ip, nickname, s):
        # 유저 IP에 해당하는 닉네임과 상태 정보 삭제
        sql = f'DELETE FROM state WHERE ip="{user_ip}";'
        self.execute_db(sql)

        # 유저 IP에 해당하는 닉네임과 상태 정보 생성
        sql = f'INSERT INTO state VALUES ("{user_ip}", "{nickname}", 9000);'
        self.execute_db(sql)

        message = json.dumps(['/set_nickname_complete', nickname])
        s.send(message.encode())

    # DB 작업
    @staticmethod
    def execute_db(sql):
        conn = pymysql.connect(user='elisa', password='0000', host='10.10.21.108', port = 3306, database='chatandgame')
        c = conn.cursor()

        # 인수로 받아온 쿼리문에 해당하는 작업 수행
        c.execute(sql)
        # 커밋
        conn.commit()

        c.close()
        conn.close()

        # 결과 반환
        return c.fetchall()


if __name__ == '__main__':
    main_server = MainServer
    main_server()
