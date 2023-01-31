import socket
import sys

import pymysql
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLineEdit

room_ui = uic.loadUiType('room.ui')[0]
qt_ui = uic.loadUiType('main.ui')[0]


class MainWindow(QMainWindow, qt_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.chat_client = ChatClient()

        self.set_nickname.clicked.connect(self.setup_nickname)

    def setup_nickname(self):
        if self.nickname_input.text() == '':
            QMessageBox.warning(self, '닉네임 미기입', '닉네임을 입력하세요.')

        else:
            sql = f'DELETE FROM state WHERE ip="{socket.gethostbyname(socket.gethostname())}"'
            db_run(sql)

            sql = f'''INSERT INTO state VALUES ("{socket.gethostbyname(socket.gethostname())}", 
            "{self.nickname_input.text()}", "1")'''
            db_run(sql)

        self.nickname_input.clear()

class ChatClient(QMainWindow, room_ui):
    def __init__(self):
        super().__init__()


def db_run(sql):
    conn = pymysql.connect(user='elisa', password='0000', host='10.10.21.108', port = 3306, database='chatandgame')
    c = conn.cursor()

    c.execute(sql)
    conn.commit()

    c.close()
    conn.close()

    return c.fetchall()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()
