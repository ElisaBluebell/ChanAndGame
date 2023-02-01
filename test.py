import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from socket import *
from threading import *
import json

form_class = uic.loadUiType("main.ui")[0]
ip = '10.10.21.108'
port = 9000


class WindowClass(QMainWindow, form_class):
    def __init__(self, sip, sport):
        super().__init__()
        self.setupUi(self)

        self.initialize_socket(sip, sport)

        self.make_room.clicked.connect(self.roommake)
        self.set_nickname.clicked.connect(self.nickmake)

    # 서버에 통신 연결 및 닉네임 확인
    def initialize_socket(self, sip, sport):
        self.c = socket(AF_INET, SOCK_STREAM)
        self.c.connect((sip, sport))
        r_msg = self.c.recv(1024)
        if r_msg:
            self.nickname.setText(f'{r_msg.decode()}님 환영합니다.')

    # 방만들기
    def roommake(self):
        print('아직')

    # 닉네임 설정 하기
    def nickmake(self):
        nick = self.nickname_input.text()
        if nick:
            msg = ['닉네임', nick]
            msg = json.dumps(msg)
            self.c.sendall(msg.encode())
            r_msg = self.c.recv(1024)
            print(r_msg.decode())
            if r_msg.decode() == 'True':
                self.nickname.setText(f'{nick}님 환영합니다.')
                self.nickname_input.clear()
            else:
                QMessageBox.information(self, '안내창', '닉네임이 중복되었습니다.')
                self.nickname_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass(ip, port)
    myWindow.show()
    app.exec_()
