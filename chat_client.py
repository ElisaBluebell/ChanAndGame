import socket
import sys
import pymysql
import datetime

from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

room_ui = uic.loadUiType('room.ui')[0]
qt_ui = uic.loadUiType('main.ui')[0]


class MainWindow(QMainWindow, qt_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.chat_client = ChatClient()

        self.show_user_list()
        self.show_nickname()

        self.set_nickname.clicked.connect(self.setup_nickname)
        self.make_room.clicked.connect(self.make_chat_room)

    def setup_nickname(self):
        if self.nickname_input.text() == '':
            QMessageBox.warning(self, '닉네임 미기입', '닉네임을 입력하세요.')

        else:
            # 내 IP에 해당하는 닉네임과 상태 정보 삭제
            sql = f'DELETE FROM state WHERE ip="{socket.gethostbyname(socket.gethostname())}"'
            execute_db(sql)

            # 내 IP에 해당하는 닉네임과 상태 정보 생성
            sql = f'''INSERT INTO state VALUES ("{socket.gethostbyname(socket.gethostname())}", 
            "{self.nickname_input.text()}", "1")'''
            execute_db(sql)

        self.nickname_input.clear()
        self.show_user_list()
        self.show_nickname()

    # DB에서 현재 상태가 1(로그인이라고 가정)인 유저들을 불러와서 accessor_list에 출력함
    def show_user_list(self):
        sql = 'SELECT 닉네임 FROM state WHERE 상태="1"'
        login_user_list = execute_db(sql)

        login_user = QStandardItemModel()

        for user in login_user_list:
            login_user.appendRow(QStandardItem(user[0]))

        self.accessor_list.setModel(login_user)

    def show_nickname(self):
        nickname = ''

        try:
            # 내 IP에 해당하는 닉네임을 DB에서 불러옴
            sql = f'SELECT 닉네임 FROM state WHERE IP="{socket.gethostbyname(socket.gethostname())}"'
            nickname = execute_db(sql)[0][0]

        # DB에 데이터가 없을 경우 무시하고 진행
        except IndexError:
            pass

        if not nickname:
            self.nickname.setText('닉네임을 설정해주세요.')

        else:
            self.nickname.setText(f'{nickname}')

    def make_chat_room(self):
        if self.check_have_room() == 1:
            QMessageBox.information(self, '생성 불가', '이미 생성된 방이 있습니다.')

        else:
            # 빈 방 체크
            empty_room_number = self.empty_number_checker('방번호', 1, 100)
            empty_port = self.empty_number_checker('port', 55000, 55100)

            sql = f'''INSERT INTO chat VALUES ({empty_room_number}, "{self.nickname.text()}", 
            "{str(datetime.datetime.now())[:-7]}", "님이 채팅방을 생성하였습니다.", 
            "{socket.gethostbyname(socket.gethostname())}", "{empty_port}")'''
            execute_db(sql)

            self.chat_client.show()

    # 빈 숫자 확인을 위한 함수, 매개변수(칼럼명, 시작값, 종료값)
    def empty_number_checker(self, item, start, end):
        sql = f'SELECT {item} FROM chat'
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

    def check_have_room(self):
        sql = f'''SELECT 생성자 FROM chat'''
        temp = execute_db(sql)

        for room_maker in temp:
            if socket.gethostbyname(socket.gethostname()) == room_maker[0]:
                return 1

        return 0


class ChatClient(QMainWindow, room_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def setup_chatroom(self):
        pass

    def connect_server(self):
        pass

    def invite_user(self):
        pass

    def receive_chat(self):
        pass

    def send_chat(self):
        pass

    def show_user(self):
        pass


# DB 작업
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
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()
