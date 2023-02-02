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
                        # 받아온 바이트 데이터를 디코딩
                        data = s.recv(self.BUFFER).decode()
                        # 송신자와 데이터 확인을 위해 콘솔창 출력
                        print(f'Received: {s.getpeername()}: {data}')

                        # 실제 데이터를 수신한 경우
                        if data:
                            # 데이터 자료형 복원
                            message = eval(data)
                            # 명령 실행 함수로 이동(송신자와, 데이터를 가지고)
                            self.command_processor(s.getpeername()[0], message, s)
                            # # 수신한 명령 에코
                            # command_taken = json.dumps(['the last command was' + message[0], message[1]])
                            # s.send(command_taken.encode())

                        # 유언을 받은 경우
                        if not data:
                            # 시체를 안고 커넥션 로스트 함수로
                            self.connection_lost(s)
                            continue

                    except ConnectionResetError:
                        self.connection_lost(s)
                        continue

    def connection_lost(self, s):
        # DB상 유저 상태 변경 함수 실행
        self.set_user_status_logout(s.getpeername()[0])
        # 커넥션 로스트 상태 확인을 위한 출력
        print(f'Client{s.getpeername()} is offline')
        # 해당 커넥션 소켓 닫음
        s.close()
        # 소켓 리스트에서 삭제
        self.sock_list.remove(s)

    def command_processor(self, user_ip, message, s):
        # 메세지 확인을 위한 출력
        print(f'메시지: {message}')
        print(type(message))

        # 명령문과 컨텐츠 구분
        command = message[0]
        content = message[1]

        # 커맨드에 해당하는 명령 실행
        if command == '/setup_nickname':
            # DB상 클라이언트 닉네임 변경
            self.setup_nickname(user_ip, content, s)

        elif command == '/check_nickname_exist':
            self.check_nickname_exist(content, s)

        elif command == '/get_main_user_list':
            self.get_main_user_list(s)

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
        try:
            nickname = self.execute_db(sql)[0][0]

        # DB에 등록된 닉네임이 없어 IndexError가 뜰 경우 nickname은 ''으로 설정해서 전송
        except IndexError:
            nickname = ''

        # 닉네임 라벨 설정을 명령하는 메세지 설정
        data = json.dumps(['/set_nickname_label', nickname])
        # 자료형 변환하여 전송
        c_sock.send(data.encode())

    def check_nickname_exist(self, nickname, s):
        checker = 0
        sql = 'SELECT 닉네임 FROM state;'
        temp = self.execute_db(sql)

        for i in range(len(temp)):
            if nickname == temp[i][0]:
                data = json.dumps(['/nickname_exists', ''])
                s.send(data.encode())
                checker = 1

        if checker == 0:
            data = json.dumps(['/setup_nickname', nickname])
            s.send(data.encode())

    def setup_nickname(self, user_ip, nickname, s):
        # 유저 IP에 해당하는 닉네임과 상태 정보 삭제
        self.delete_nickname_from_database(user_ip)

        # 유저 IP에 해당하는 닉네임과 상태 정보 생성
        self.create_nickname_in_database(user_ip, nickname)

        # 닉네임 세팅 종료를 알리는 메세지 설정 및 전송
        data = json.dumps(['/set_nickname_complete', nickname])
        s.send(data.encode())

    def delete_nickname_from_database(self, user_ip):
        sql = f'DELETE FROM state WHERE ip="{user_ip}";'
        self.execute_db(sql)

    def create_nickname_in_database(self, user_ip, nickname):
        sql = f'INSERT INTO state VALUES ("{user_ip}", "{nickname}", 9000);'
        self.execute_db(sql)

    def send_message(self):
        pass

    def get_main_user_list(self, s):
        sql = 'SELECT 닉네임 FROM state WHERE port=9000;'
        temp = self.execute_db(sql)
        login_user_list = self.array_user_list(temp)
        self.send_main_user_list(login_user_list, s)

    def array_user_list(self, temp):
        login_user_list = []

        for i in range(len(temp)):
            login_user_list.append(temp[i][0])
        return login_user_list

    def send_main_user_list(self, user_list, s):
        data = json.dumps(['/set_user_list', user_list])
        print(data)
        s.send(data.encode())

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
