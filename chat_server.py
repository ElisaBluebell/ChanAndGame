import datetime
import json
import pymysql
import socket
import select
import time
import random

class MainServer:

    # 초기 세팅

    def __init__(self):
        # 소켓 리스트
        self.client_list = []
        self.chat_list = []
        self.server_list = []

        # 서버 소켓 생성
        self.s_sock = socket.socket()
        # 데이터 사이즈
        self.BUFFER = 1024
        # 서버 오픈을 위한 포트와 아이피
        self.ip = socket.gethostbyname(socket.gethostname())
        self.port = 9000
        # 스무고개 턴수
        self.game_over = 20

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

        # 소켓 리스트와 서버 소켓 리스트에 서버 소켓 추가
        self.client_list.append(self.s_sock)
        self.server_list.append(self.s_sock)
        # 채팅 소켓 초기 설정 함수 호출
        self.initialize_chat_socket()
        # 포트 번호를 알림
        print(f'Waiting Connections on Port {self.port}...')

    # 채팅 소켓 설정 함수
    def initialize_chat_socket(self):
        # 9001번 포트부터 9100번 포트까지 사용
        for i in range(9001, 9101):
            # 각각의 포트를 반복문을 활용해 소켓 객체로 선언
            globals()['port' + str(i)] = socket.socket()

            # 소켓 초기 설정 및 입력 대기
            globals()['port' + str(i)].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            globals()['port' + str(i)].bind((self.ip, i))
            globals()['port' + str(i)].listen()

            # 소켓 리스트와 서버 소켓 리스트에 반복생성한 함수 추가
            self.client_list.append(globals()['port' + str(i)])
            self.server_list.append(globals()['port' + str(i)])

    # 명령문 받기 함수
    def receive_command(self):
        while True:
            # 읽기, 쓰기, 오류 소켓 리스트를 넌블로킹 모드로 선언
            r_sock, w_sock, e_sock = select.select(self.client_list, [], [], 0)
            for s in r_sock:
                if s in self.server_list:
                    # 접속받은 소켓과 주소 설정
                    c_sock, addr = s.accept()
                    # 접속받은 소켓에 대한 설정 진행
                    self.set_client(c_sock, addr, s)

                else:
                    try:
                        # 받아온 바이트 데이터를 디코딩
                        data = s.recv(self.BUFFER).decode('utf-8')
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

    # 클라이언트 소켓 접속시 행해지는 기본설정들
    def set_client(self, c_sock, addr, s):
        # 클라이언트 소켓을 소켓 리스트에 추가함
        self.client_list.append(c_sock)
        self.chat_list.append(c_sock)
        # 해당 주소의 접속을 콘솔에 출력
        print(f'Client{addr} connected')
        # 클라이언트의 초기 설정 요청
        self.set_client_default(c_sock, addr[0], s.getsockname()[1])

    def set_client_default(self, c_sock, ip, port):
        # 접속한 유저의 DB상 포트 번호를 현재 접속한 포트 번호로 변경
        self.set_user_status_login(ip, port)
        # 포트 번호 9000번(메인 페이지 접속중)일 시
        if port == 9000:
            # 클라이언트의 닉네임 라벨 설정 함수 호출
            self.set_client_nickname_label(c_sock, ip)

    # 접속한 유저의 IP를 매개로 유저 DB의 포트 번호 설정
    def set_user_status_login(self, ip, port):
        sql = f'UPDATE state SET port={port} WHERE ip="{ip}"'
        self.execute_db(sql)

    def set_client_nickname_label(self, c_sock, ip):
        # DB에서 클라이언트의 ip에 해당하는 닉네임을 추출
        sql = f'SELECT 닉네임 FROM state WHERE ip="{ip}"'
        try:
            nickname = self.execute_db(sql)[0][0]

        # DB에 등록된 닉네임이 없어 IndexError가 뜰 경우 nickname은 ''으로 설정
        except IndexError:
            nickname = ''

        # 정상적으로 등록된 닉네임이 있을 경우 닉네임 설정 완료 전송
        self.send_command('/set_nickname_complete', nickname, c_sock)

    # 연결 소실시 행해지는 작업
    def connection_lost(self, s):
        # DB상 유저 상태 변경 함수 실행
        self.set_user_status_logout(s.getpeername()[0])
        # 커넥션 로스트 상태 확인을 위한 출력
        print(f'Client{s.getpeername()} is offline')
        # 해당 커넥션 소켓 닫음
        s.close()
        # 소켓 리스트에서 삭제
        self.client_list.remove(s)
        self.chat_list.remove(s)

    # 접속 종료한 유저의 IP를 매개로 포트 번호 초기화
    def set_user_status_logout(self, ip):
        sql = f'UPDATE state SET port=0 WHERE ip="{ip}"'
        self.execute_db(sql)

    # 명령문 전송
    @staticmethod
    def send_command(command, content, s):
        data = json.dumps([command, content])
        s.send(data.encode())

    # DB 작업
    @staticmethod
    def execute_db(sql):
        conn = pymysql.connect(user='elisa', password='0000', host='10.10.21.108', port=3306, database='chatandgame')
        c = conn.cursor()

        # 인수로 받아온 쿼리문에 해당하는 작업 수행
        c.execute(sql)
        # 커밋
        conn.commit()

        c.close()
        conn.close()

        # 결과 반환
        return c.fetchall()

    # 초기 설정 종료

    # 이하 명령문 송수신

    # 명령문 커넥션
    def command_processor(self, user_ip, message, s):
        # 명령문과 컨텐츠 구분
        command = message[0]
        content = message[1]

        # 이하 각 커맨드에 해당하는 명령 실행
        if command == '/setup_nickname':
            self.setup_nickname(user_ip, content, s)

        elif command == '/check_nickname_exist':
            self.check_nickname_exist(content, s)

        elif command == '/show_user':
            self.show_user(content, s)

        elif command == '/get_room_list':
            self.get_room_list(s)

        elif command == '/make_chat_room':
            self.make_chat_room(user_ip, content, s)

        elif command == '/request_port':
            self.give_port(content, s)

        elif command == '/load_chat':
            self.load_chat(content, s)

        elif command == '/show_member':
            self.get_member_list(content[0], content[1], s)

        elif command == '/invitation':
            self.invite( content[0], content[1])

        elif command == '/chat':
            self.chat_process(user_ip, content, s)

        elif command == '/refuse':
            self.refuse(s)

        elif command == '/set_game':
            self.check_game_entrant(content, s)

        elif command == '/topic_selection':
            self.set_topic(content[0], content[1])

        else:
            pass

    # /setup_nickname 명령문
    def setup_nickname(self, user_ip, nickname, s):
        # 유저 IP에 해당하는 닉네임과 상태 정보 삭제
        self.delete_nickname_from_database(user_ip)

        # 유저 IP에 해당하는 닉네임과 상태 정보 생성
        self.create_nickname_in_database(user_ip, nickname)

        # 닉네임 세팅 종료를 알리는 메세지 설정 및 전송
        self.send_command('/set_nickname_complete', nickname, s)

    # 유저 정보 DB 삭제
    def delete_nickname_from_database(self, user_ip):
        sql = f'DELETE FROM state WHERE ip="{user_ip}";'
        self.execute_db(sql)

    # 유저 정보 DB 생성
    def create_nickname_in_database(self, user_ip, nickname):
        sql = f'INSERT INTO state VALUES ("{user_ip}", "{nickname}", 9000);'
        self.execute_db(sql)

    # /check_nickname_exists 명령문
    # 닉네임의 중복을 확인하고 닉네임 설정을 요청함
    def check_nickname_exist(self, nickname, s):
        # 닉네임 중복 유무 확인을 위한 변수 선언
        checker = 0
        # DB에서 모든 닉네임을 추출
        sql = 'SELECT 닉네임 FROM state;'
        temp = self.execute_db(sql)

        # 불러온 닉네임들이 클라이언트에서 보내온 닉네임과 일치하는지 확인
        for i in range(len(temp)):
            # 일치하는 경우 닉네임 중복임을 클라이언트에 알림
            if nickname == temp[i][0]:
                self.send_command('/nickname_exists', '', s)
                checker = 1

        # 일치하는 닉네임이 없을 경우 클라이언트의 닉네임으로 설정을 허가함
        if checker == 0:
            self.send_command('/setup_nickname', nickname, s)

    def get_single_item_list(self, item, table, key_column, key):
        sql = f'SELECT {item} FROM {table} WHERE {key_column}={key};'
        temp = self.execute_db(sql)
        return temp

    # /show_user 명령문
    # DB에서 해당 채팅방에 접속한 유저 리스트를 불러와 클라이언트에 유저 리스트 출력 명령과 함께 전송
    def show_user(self, port, s):
        chat_user_list = self.get_single_item_list('닉네임', 'state', 'port', port)
        chat_user_list = self.array_list(chat_user_list)
        self.send_command('/set_user_list', chat_user_list, s)

    # 반복문을 활용해 인수로 받은 유저 정보를 리스트로 만들어 반환
    @staticmethod
    def array_list(temp):
        temp_list = []

        for i in range(len(temp)):
            temp_list.append(temp[i][0])

        return temp_list

    # /get_room_list 명령문
    # DB를 통해 현재 개설된 채팅방의 정보를 정리하여 클라이언트에게 전달
    def get_room_list(self, s):
        sql = 'SELECT DISTINCT a.port, b.닉네임 FROM chat AS a INNER JOIN state AS b on a.생성자=b.ip;'
        temp = self.execute_db(sql)
        # 반복문을 활용해 유저 정보를 리스트로 만들어서 전송
        room_list = self.array_room_list(temp)
        self.send_command('/set_room_list', room_list, s)

    # 리스트화 로직은 array_user_list 함수와 같으나 DB에서 가져온 묶음 형태의 데이터를 그대로 전송하기에 신규 작성함
    @staticmethod
    def array_room_list(temp):
        room_list = []

        for i in range(len(temp)):
            room_list.append(temp[i])

        return room_list

    # /make_chat_room 명령문
    # 채팅방 생성 및 입장
    def make_chat_room(self, user_ip, nickname, s):
        # 해당 유저의 방 개설 정보 확인
        if self.check_have_room(user_ip) == 1:
            # 방이 이미 존재할 경우 중복 생성 불가함을 클라이언트에게 전달
            self.send_command('/room_already_exists', '', s)

        # 해당 유저가 방을 개설하지 않았을 경우
        else:
            # 빈 방 번호와 부여할 포트 번호 체크, 방 번호는 1번부터 100번까지, 포트 번호는 9001번부터 9100번까지 사용
            empty_port = self.empty_number_checker('port', 9001, 9101)

            # 채팅방 DB를 만들고
            self.make_chat_room_db(nickname, empty_port)
            # 해당 채팅방 개설과 관련된 작업을 클라이언트에게 지시
            self.send_command('/open_chat_room', empty_port, s)

    # 생성자 IP 정보를 DB에서 받아와서 현재 접속 IP와 대조함, 일치시 1, 일치하는 값 없을 시 0 반환
    def check_have_room(self, user_ip):
        sql = f'''SELECT 생성자 FROM chat;'''
        temp = self.execute_db(sql)

        for room_maker in temp:
            if user_ip == room_maker[0]:
                return 1
        return 0

    # 빈 숫자 확인을 위한 함수, 매개변수(칼럼명, 시작값, 종료값)
    def empty_number_checker(self, item, start, end):
        sql = f'SELECT {item} FROM chat;'
        number_list = self.execute_db(sql)

        # 시작값부터 종료값까지 반복문을 실행해 중간에 비어있는 값을 찾는다.
        for i in range(start, end):
            # 번호 존재를 체크하기 위한 변수 선언
            checker = 0

            # DB에서 받아온 번호가 i값과 같을 시 반복문 정지
            for number in number_list:
                if number[0] == i:
                    checker = 1
                    break

            # i값과 동일한 번호가 없을 경우 i값 반환
            if checker == 0:
                return i

    # 닉네임, 빈 방 번호와 빈 포트 번호를 받아 DB에 해당하는 채팅방 정보 작성
    def make_chat_room_db(self, nickname, empty_port):
        sql = f'''INSERT INTO chat VALUES ("{nickname}", 
        "{str(datetime.datetime.now())[:-7]}", "님이 채팅방을 생성하였습니다.", 
        "{socket.gethostbyname(socket.gethostname())}", "{empty_port}");'''
        self.execute_db(sql)

    # /give_port 명령문
    # DB에 기록된 채팅방의 생성자 IP를 매개로 채팅방의 포트 번호를 불러와 클라이언트에게 전달
    def give_port(self, nickname, s):
        sql = f'SELECT port FROM chat WHERE 생성자=(SELECT ip FROM state WHERE 닉네임="{nickname}")'
        port = self.execute_db(sql)[0][0]

        self.send_command('/open_chat_room', port, s)

    # /load_chat 명령문
    # DB에서 채팅 기록을 로드하여 클라이언트에게 전달
    def load_chat(self, chat_port, s):
        # 최근 채팅 내역을 저장해줄 리스트 선언
        recent_chat = []

        try:
            sql = f'SELECT * FROM chat WHERE port={chat_port} ORDER BY 시간 LIMIT 10;'
            temp = self.execute_db(sql)
            print(temp)
            # 0=방번호, 1=닉네임, 2시간, 3=채팅내용, 4=생성자, 5=포트 // 시간 닉네임 생성자 순으로 정렬
            for i in range(len(temp)):
                if temp[i][3] == '님이 채팅방을 생성하였습니다':
                    recent_chat.append([temp[i][1][11:-3], temp[i][0], temp[i][2]])
                else:
                    recent_chat.append([temp[i][1][11:-3], temp[i][0], f': {temp[i][2]}'])

        finally:
            pass

        self.send_command('/load_recent_chat', recent_chat, s)

    def chat_process(self, user, chat, s):
        room_creator = self.seek_room_creator(s)
        # self.insert_chat_in_db(user, chat, room_creator, s)
        self.fire_the_chat(user, chat, s)

    def seek_room_creator(self, s):
        sql = f'SELECT 생성자 FROM chat WHERE port={s.getsockname()[1]}'
        return self.execute_db(sql)[0][0]

    def insert_chat_in_db(self, user, chat, room_creator, s):
        sql = f'''INSERT INTO chat VALUES (
        (SELECT 닉네임 FROM state WHERE ip='{user}'), 
        '{str(datetime.datetime.now())[:-7]}', 
        '{chat}', 
        '{room_creator}', 
        {s.getsockname()[1]}
        )'''
        self.execute_db(sql)

    def fire_the_chat(self, user, chat, s):
        user = self.get_user_name(user)
        data = f'[{str(datetime.datetime.now())[11:-10]}]{user}: {chat}'
        same_port_user = self.select_same_port_user(s)

        for sock in same_port_user:
            print(sock)
            print(self.s_sock)
            self.send_command('/print_chat', data, sock)
            # time.sleep(0.2)

    def get_user_name(self, user):
        sql = f'SELECT 닉네임 FROM state WHERE ip="{user}"'
        return self.execute_db(sql)[0][0]

    def select_same_port_user(self, s):
        same_port_user = []
        for sock in self.chat_list:
            if sock.getsockname()[1] == s.getsockname()[1]:
                same_port_user.append(sock)
                print(sock.getsockname())

        return same_port_user

    # 채팅창에서 참가자 및 초대 가능한 사람 보여주기
    def get_member_list(self, state, port, s):
        if state == 'True':
            self.show_user(9000, s)
        else:
            self.show_user(port, s)

    # 채팅방에 초대하기
    def invite(self, name, nickname):
        sql = f"select ip from state where 닉네임 ='{name}';"
        invite_ip = self.execute_db(sql)[0][0]
        for i in self.client_list:
            try:
                if invite_ip in i.getpeername():
                    self.send_command('/invitation', nickname, i)
            except:
                continue

    # 초대 거절 메시지
    def refuse(self, s):
        self.send_command('/refuse', '', s)

    # 게임 초기 셋팅
    def check_game_entrant(self, port, s):
        sql = f"select ip, 닉네임 from state where port = '{port}';"
        member = self.execute_db(sql)
        # if len(member) < 2:
        #     self.send_command('/understaffed', '', s)
        # else:
        self.entrant_socket = []
        presenter = random.choice(member)
        for client_socket in self.client_list:
            try:
                for value in member:
                    if value == presenter:
                        self.send_command('/presenter', '', client_socket)
                        self.presenter_socket = client_socket
                    elif value[0] in client_socket.getpeername():
                        self.send_command('/entrant', '', client_socket)
                        self.entrant_socket.append(client_socket)
            except:
                continue
        random.shuffle(self.entrant_socket)
        self.game_trun = 0

    # 주제 및 정답 정하기
    def set_topic(self, topic, problem):
        self.answer = problem
        for entrant in self.entrant_socket:
            self.send_command('/topic', topic, entrant)


# 돌아라 돌아 ~.~
if __name__ == '__main__':
    main_server = MainServer
    main_server()
