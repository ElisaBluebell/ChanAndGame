import sys
import threading
import time

from PyQt5.QtWidgets import *
from PyQt5 import uic
from socket import *
from threading import *
import json

room_ui = uic.loadUiType('room.ui')[0]
form_class = uic.loadUiType("main.ui")[0]
ip = '10.10.21.108'
port = 9000


class WindowClass(QMainWindow, form_class):
    def __init__(self, sip, sport):
        super().__init__()
        self.setupUi(self)
        self.show()
        self.ip = sip

        self.make_room.clicked.connect(self.roommake)
        self.set_nickname.clicked.connect(self.nickmake)
        # 서버에 통신 연결
        self.c = socket(AF_INET, SOCK_STREAM)
        self.c.connect((sip, sport))
        # 스레드 동작
        self.thread_start()

    def thread_start(self):
        cth = Thread(target=self.reception, args=(self.c,))
        cth.start()

    def reception(self, c):
        while True:
            r_msg = c.recv(1024)
            r_msg = json.loads(r_msg.decode())
            if r_msg[0] == '초기닉네임':
                if r_msg == '닉네임을 설정해주세요.':
                    self.nickname.setText(f'{r_msg[1]}')
                else:
                    self.nickname.setText(f'{r_msg[1]}님 환영합니다.')
            elif r_msg[0][0] == '닉네임':
                if r_msg[1] == 'True':
                    self.nickname.setText(f'{r_msg[0][1]}님 환영합니다.')
                    self.nickname_input.clear()
                else:
                    self.nickname_input.clear()
            elif r_msg[0] == '목록':
                self.accessor_list.clear()
                self.room_list.clear()
                for i in r_msg[1]:
                    self.accessor_list.addItem(f'{i[1]}[{i[0]}, {i[2]}]')
                for i in r_msg[2]:
                    self.room_list.addItem(f'{i[0]}번 방, {i[1]}님의 방입니다.')
            elif r_msg[0] == '방생성':
                if r_msg[1] == 'True':
                    print(f'{r_msg[2]}방 생성')
                    self.chatroom = ChatClient(self, self.ip, r_msg[2])
                else:
                    print('방있음')
            else:
                print('접속 종료')
                break

    # 방만들기
    def roommake(self):
        msg = json.dumps(['방만들기'])
        self.c.sendall(msg.encode())

    # 닉네임 설정 하기
    def nickmake(self):
        nick = self.nickname_input.text()
        if nick:
            msg = json.dumps(['닉네임', nick])
            self.c.sendall(msg.encode())

    def closeEvent(self, e):
        msg = json.dumps(['나감'])
        self.c.sendall(msg.encode())


class ChatClient(QMainWindow, room_ui):
    def __init__(self, parent, ip, port):
        super().__init__()
        self.setupUi(self)

        self.p = parent
        self.c = socket(AF_INET, SOCK_STREAM)
        self.c.connect((ip, port))
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass(ip, port)
    app.exec_()
