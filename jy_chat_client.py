import socket
import sys
import pymysql
import datetime

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLabel, QListWidget

room_ui = uic.loadUiType('room.ui')[0]
qt_ui = uic.loadUiType('main.ui')[0]


class MainWindow(QMainWindow, qt_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # 라벨 생성
        self.welcome = QLabel(self)

        # 클래스 선언
        self.chat_client = ChatClient()

        # 대기실(port=9000) 초기과 함수
        self.show_user_list()
        self.show_room_list()
        self.show_nickname()

        # 시그널 - 메서드
        # 닉네임 선택
        self.set_nickname.clicked.connect(self.setup_nickname)
        # 방 생성
        self.make_room.clicked.connect(self.make_chat_room)
        # 방 입장
        self.room_list.clicked.connect(self.enter_chat_room)

    # 닉네임 선택
    def setup_nickname(self):
        # 닉네임 입력창 입력 유무 확인
        if self.nickname_input.text() == '':
            QMessageBox.warning(self, '닉네임 미기입', '닉네임을 입력하세요.')

        else:
            # 닉네임 중복
            if self.check_nickname_exist() == 1:
                QMessageBox.warning(self, '닉네임 중복', '이미 존재하는 닉네임입니다.')
            # 닉네임 변경
            else:
                # 내 IP에 해당하는 닉네임과 상태 정보 삭제
                sql = f'DELETE FROM state WHERE ip="{socket.gethostbyname(socket.gethostname())}";'
                execute_db(sql)

                # 내 IP에 해당하는 닉네임과 상태 정보 생성
                sql = f'''INSERT INTO state VALUES ("{socket.gethostbyname(socket.gethostname())}", 
                "{self.nickname_input.text()}", "9000");'''
                execute_db(sql)

        # 변경된 닉네임으로 초기화
        self.nickname_input.clear()
        self.show_user_list()
        self.show_nickname()

    # 닉네임 중복 여부 확인
    def check_nickname_exist(self):
        sql = 'SELECT 닉네임 FROM state;'
        temp = execute_db(sql)
        for i in range(len(temp)):
            if self.nickname_input.text() == temp[i][0]:
                return 1
        return 0

    # DB에서 현재 상태가 대기중(port = 9000)인 유저들을 불러와서 accessor_list에 출력함
    def show_user_list(self):
        self.accessor_list.clear()
        sql = 'SELECT 닉네임 FROM state WHERE port="9000";'
        login_user_list = execute_db(sql)

        for i in range(len(login_user_list)):
            self.accessor_list.insertItem(i, login_user_list[i][0])

    # DB에서 현재 만들어진 방의 내역을 불러온다.
    def show_room_list(self):
        self.room_list.clear()
        sql = 'SELECT DISTINCT 방번호, 생성자 FROM chat;'
        temp = execute_db(sql)

        for i in range(len(temp)):
            self.room_list.insertItem(i, f'{temp[i][1]}님의 방')

    # 대기실 에서 닉네임 보여주기
    def show_nickname(self):
        nickname = ''

        try:
            # 내 IP에 해당하는 닉네임을 DB에서 불러옴
            sql = f'SELECT 닉네임 FROM state WHERE IP="{socket.gethostbyname(socket.gethostname())}";'
            nickname = execute_db(sql)[0][0]

        # DB에 데이터가 없을 경우 무시하고 진행
        except IndexError:
            pass

        if not nickname:
            self.nickname.setText('닉네임을 설정해주세요.')

        else:
            self.nickname.setText(f'{nickname}')
            self.welcome.setText('님 환영합니다.')
            self.welcome.setGeometry(len(nickname) * 12 + 710, 10, 85, 16)

    # 방 만들기
    def make_chat_room(self):
        # 방을 만들었는지 확인
        if self.check_have_room() == 1:
            QMessageBox.information(self, '생성 불가', '이미 생성된 방이 있습니다.')

        else:
            # 새 방을 만들 번호와 port 찾기
            empty_room_number = self.empty_number_checker('방번호', 1, 100)
            empty_port = self.empty_number_checker('port', 9001, 9100)

            # DB에 채팅방 등록
            sql = f'''INSERT INTO chat VALUES ({empty_room_number}, "{self.nickname.text()}", 
            "{str(datetime.datetime.now())[:-7]}", "님이 채팅방을 생성하였습니다.", 
            "{socket.gethostbyname(socket.gethostname())}", "{empty_port}");'''
            execute_db(sql)

            self.chat_client.show()
            self.show_room_list()

    # 빈 숫자 확인을 위한 함수, 매개변수(칼럼명, 시작값, 종료값)
    def empty_number_checker(self, item, start, end):
        sql = f'SELECT {item} FROM chat;'
        number_list = execute_db(sql)

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

    # 방 개설 여부 확인
    def check_have_room(self):
        # 생성자 IP 정보를 DB에서 받아와서 현재 접속 IP와 대조함, 일치시 1, 일치하는 값 없을 시 0 반환
        sql = f'''SELECT 생성자 FROM chat;'''
        temp = execute_db(sql)

        for room_maker in temp:
            if socket.gethostbyname(socket.gethostname()) == room_maker[0]:
                return 1
        return 0

    # 방 입장하기
    def enter_chat_room(self):
        reply = QMessageBox.question(self, '입장 확인', '채팅방에 입장 하시겠습니까?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            user_name = self.room_list.currentItem().text().split('님의 방')[0]
            # 아직 IP로 표시되기 때문에 유저명이 아닌 IP를 일단 불러옴
            sql = f'SELECT port FROM chat WHERE 생성자="{user_name}";'
            port = execute_db(sql)[0][0]

            self.chat_client.show()

        else:
            pass


# 방 입장후 클래스
class ChatClient(QMainWindow, room_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # 초기화 함수
        self.setup_chatroom()

    def setup_chatroom(self):
        self.chat_list.clear()
        self.show_user()
        self.load_chat()

    def load_chat(self):
        # 통신 미적용으로 인해 임의로 9001번 포트 줌
        sql = f'SELECT * FROM chat WHERE port=9001 LIMIT 1;'
        chat_log = execute_db(sql)
        print(chat_log)
        # self.chat_list = QListWidget
        self.chat_list.insertItem(0, f'[{chat_log[0][2]}]에 {chat_log[0][1]}{chat_log[0][3]}')

    def show_user(self):
        pass

    def connect_server(self):
        pass

    def invite_user(self):
        pass

    def receive_chat(self):
        pass

    def send_chat(self):
        pass


# DB 작업
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()
