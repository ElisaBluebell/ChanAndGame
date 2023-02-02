import datetime
import json
import pymysql
import socket
import select


class MainServer:
    def __init__(self):
        # 소켓 리스트
        self.sock_list = []

        self.server_list = []

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
        self.server_list.append(self.s_sock)
        self.initialize_chat_socket()
        # 포트 번호를 알림
        print(f'Waiting Connections on Port {self.port}...')

    def initialize_chat_socket(self):
        for i in range(9001, 9101):
            globals()['port' + str(i)] = socket.socket()

            globals()['port' + str(i)].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            globals()['port' + str(i)].bind((self.ip, i))
            globals()['port' + str(i)].listen()

            self.sock_list.append(globals()['port' + str(i)])
            self.server_list.append(globals()['port' + str(i)])

    def receive_command(self):
        while True:
            # 읽기, 쓰기, 오류 소켓 리스트를 넌블로킹 모드로 선언
            r_sock, w_sock, e_sock = select.select(self.sock_list, [], [], 0)
            for s in r_sock:
                if s in self.server_list:
                    # 접속받은 소켓과 주소 설정
                    c_sock, addr = s.accept()
                    # 클라이언트 소켓을 소켓 리스트에 추가함
                    self.sock_list.append(c_sock)
                    # 해당 주소의 접속을 콘솔에 출력
                    print(f'Client{addr} connected')
                    # 클라이언트의 초기 설정
                    self.set_client_default(c_sock, addr[0], s.getsockname()[1])

                else:
                    try:
                        print(s)
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

                        # 유언을 받은 경우
                        if not data:
                            # 시체를 안고 커넥션 로스트 함수로
                            self.connection_lost(s)
                            continue

                    except ConnectionResetError:
                        self.connection_lost(s)
                        continue

    # 명령을 전송하는 함수
    def send_command(self, command, content, s):
        data = json.dumps([command, content])
        s.send(data.encode())

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
        # 명령문과 컨텐츠 구분
        command = message[0]
        content = message[1]
        print(f'command: {command}, content: {content}')

        # 커맨드에 해당하는 명령 실행
        if command == '/setup_nickname':
            # DB상 클라이언트 닉네임 변경
            self.setup_nickname(user_ip, content, s)

        elif command == '/check_nickname_exist':
            self.check_nickname_exist(content, s)

        elif command == '/get_main_user_list':
            self.get_main_user_list(s)

        elif command == '/get_room_list':
            self.get_room_list(s)

        elif command == '/make_chat_room':
            self.make_chat_room(user_ip, content, s)

        elif command == '/request_port':
            self.give_port(content, s)

    # /setup_nickname 명령문
    def setup_nickname(self, user_ip, nickname, s):
        # 유저 IP에 해당하는 닉네임과 상태 정보 삭제
        self.delete_nickname_from_database(user_ip)

        # 유저 IP에 해당하는 닉네임과 상태 정보 생성
        self.create_nickname_in_database(user_ip, nickname)

        # 닉네임 세팅 종료를 알리는 메세지 설정 및 전송
        self.send_command('/set_nickname_complete', nickname, s)

    def delete_nickname_from_database(self, user_ip):
        sql = f'DELETE FROM state WHERE ip="{user_ip}";'
        self.execute_db(sql)

    def create_nickname_in_database(self, user_ip, nickname):
        sql = f'INSERT INTO state VALUES ("{user_ip}", "{nickname}", 9000);'
        self.execute_db(sql)

    # /check_nickname_exists 명령문
    def check_nickname_exist(self, nickname, s):
        checker = 0
        sql = 'SELECT 닉네임 FROM state;'
        temp = self.execute_db(sql)

        for i in range(len(temp)):
            if nickname == temp[i][0]:
                self.send_command('/nickname_exists', '', s)
                checker = 1

        if checker == 0:
            self.send_command('/setup_nickname', nickname, s)

    def set_client_default(self, c_sock, ip, port):
        # 접속한 유저의 DB상 포트 번호(현재 상태)를 9000번(메인 접속, 기본)으로 변경
        self.set_user_status_login(ip, port)
        if port == 9000:
            # 클라이언트의 닉네임 라벨을 현재 접속한 ip에 맞게 변경하는 [명령문, 닉네임] 전송
            self.set_client_nickname_label(c_sock, ip)

    def set_user_status_login(self, ip, port):
        sql = f'UPDATE state SET port={port} WHERE ip="{ip}"'
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

        self.send_command('/set_nickname_label', nickname, c_sock)

    def send_message(self):
        pass

    def get_main_user_list(self, s):
        sql = 'SELECT 닉네임 FROM state WHERE port=9000;'
        temp = self.execute_db(sql)
        login_user_list = self.array_user_list(temp)
        self.send_command('/set_user_list', login_user_list, s)

    def array_user_list(self, temp):
        login_user_list = []

        for i in range(len(temp)):
            login_user_list.append(temp[i][0])

        return login_user_list

    def get_room_list(self, s):
        sql = 'SELECT DISTINCT a.방번호, b.닉네임 FROM chat AS a INNER JOIN state AS b on a.생성자=b.ip;'
        temp = self.execute_db(sql)
        room_list = self.array_room_list(temp)
        self.send_command('/set_room_list', room_list, s)

    def array_room_list(self, temp):
        room_list = []

        for i in range(len(temp)):
            room_list.append(temp[i])

        return room_list

    # 채팅방 생성 및 입장
    def make_chat_room(self, user_ip, nickname, s):
        if self.check_have_room(user_ip) == 1:
            self.send_command('/room_already_exists', '', s)

        else:
            # 빈 방 체크
            empty_room_number = self.empty_number_checker('방번호', 1, 100)
            empty_port = self.empty_number_checker('port', 9001, 9100)

            self.make_chat_room_db(nickname, empty_room_number, empty_port)
            self.send_command('/open_chat_room', empty_port, s)

    # 빈 숫자 확인을 위한 함수, 매개변수(칼럼명, 시작값, 종료값)
    def empty_number_checker(self, item, start, end):
        sql = f'SELECT {item} FROM chat;'
        number_list = self.execute_db(sql)

        # 시작값부터 종료값까지 반복문을 실행해 중간에 비어있는 값을 찾는다.
        for i in range(start, end):
            # 번호 확인을 위한 변수 선언
            checker = 0

            # DB에서 받아온 번호가 i값과 같을 시 반복문 정지
            for number in number_list:
                if number[0] == i:
                    checker = 1
                    break

            # i값과 동일한 번호가 없을 경우 i값 반환
            if checker == 0:
                return i

    def make_chat_room_db(self, nickname, empty_room_number, empty_port):
        sql = f'''INSERT INTO chat VALUES ({empty_room_number}, "{nickname}", 
        "{str(datetime.datetime.now())[:-7]}", "님이 채팅방을 생성하였습니다.", 
        "{socket.gethostbyname(socket.gethostname())}", "{empty_port}");'''
        self.execute_db(sql)

    # 방 개설 여부 확인
    def check_have_room(self, user_ip):
        # 생성자 IP 정보를 DB에서 받아와서 현재 접속 IP와 대조함, 일치시 1, 일치하는 값 없을 시 0 반환
        sql = f'''SELECT 생성자 FROM chat;'''
        temp = self.execute_db(sql)

        for room_maker in temp:
            if user_ip == room_maker[0]:
                return 1
        return 0

    def give_port(self, nickname, s):
        print(1)
        sql = f'SELECT port FROM chat WHERE 생성자=(SELECT ip FROM state WHERE 닉네임="{nickname}")'
        port = self.execute_db(sql)[0][0]

        self.send_command('/open_chat_room', port, s)

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
