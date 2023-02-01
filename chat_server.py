import json

import pymysql
import socket
import select


class MainServer:
    def __init__(self):
        # 소켓 리스트
        self.sock_list = []
        # 데이터 사이즈
        self.BUFFER = 1024
        # 서버 오픈을 위한 포트와 아이피
        self.ip = '10.10.21.121'
        self.port = 9000
        # 서버 소켓 생성
        self.s_sock = socket.socket()

        # 소켓 설정
        self.initialize_socket()
        # 명령 받기
        self.receive_command()

    # 소켓 설정 함수
    def initialize_socket(self):
        # 주소 재사용 오류 방지 옵션 부여
        self.s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 소켓 주소 설정
        self.s_sock.bind((self.ip, self.port))
        # 오픈
        self.s_sock.listen()

        # 소켓 리스트에 서버 소켓 추가
        self.sock_list.append(self.s_sock)
        # 포트 번호를 알림
        print(f'Waiting Connections on Port {self.port}...')

    def receive_command(self):
        while True:
            # 읽기, 쓰기, 오류 소켓 리스트를 넌블로킹 모드로 선언
            r_sock, w_sock, e_sock = select.select(self.sock_list, [], [], 0)
            for s in r_sock:

                if s == self.s_sock:
                    # 접속받은 소켓과 주소 설정
                    c_sock, addr = self.s_sock.accept()
                    # 클라이언트 소켓을 소켓 리스트에 추가함
                    self.sock_list.append(c_sock)
                    # 해당 주소의 접속을 콘솔에 출력
                    print(f'Client{addr} connected')
                    # 클라이언트의 초기 설정
                    self.set_client_default(c_sock, addr[0])

                else:
                    try:
                        # 받아온
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
        self.set_user_status_logout(s.getpeername()[0])
        print(f'Client{s.getpeername()} is offline')
        s.close()
        self.sock_list.remove(s)

    def command_processor(self, user_ip, message, s):
        print(f'메시지: {message}')
        print(type(message))
        command = message[0]
        content = message[1]
        if command == '/set_nickname':
            # DB상 클라이언트 닉네임 변경
            self.set_client_nickname(user_ip, content, s)

    def set_client_default(self, c_sock, ip):
        # 접속한 유저의 DB상 포트 번호(현재 상태)를 9000번(메인 접속, 기본)으로 변경
        self.set_user_status_login(ip)
        # 클라이언트의 닉네임 라벨을 현재 접속한 ip에 맞게 변경하는 [명령문, 닉네임] 전송
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

        msg = ['/set_nickname_label', nickname]
        data = json.dumps(msg)
        c_sock.send(data.encode())

    def set_client_nickname(self, user_ip, nickname, s):
        # 유저 IP에 해당하는 닉네임과 상태 정보 삭제
        self.delete_nickname_from_database(user_ip)

        # 유저 IP에 해당하는 닉네임과 상태 정보 생성
        self.create_nickname_in_database(user_ip, nickname)

        message = json.dumps(['/set_nickname_complete', nickname])
        s.send(message.encode())

    def delete_nickname_from_database(self, user_ip):
        sql = f'DELETE FROM state WHERE ip="{user_ip}";'
        self.execute_db(sql)

    def create_nickname_in_database(self, user_ip, nickname):
        sql = f'INSERT INTO state VALUES ("{user_ip}", "{nickname}", 9000);'
        self.execute_db(sql)

    def send_message(self):
        pass

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
