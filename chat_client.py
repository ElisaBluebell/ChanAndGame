import socket
import sys
import pymysql

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
            self.nickname.setText(f'{nickname}님, 환영합니다.')

    def make_chat_room(self):
        pass


class ChatClient(QMainWindow, room_ui):
    def __init__(self):
        super().__init__()


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
