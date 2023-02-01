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

        # 서버에 통신 연결
        self.c = socket(AF_INET, SOCK_STREAM)
        self.c.connect((sip, sport))

        self.make_room.clicked.connect(self.roommake)
        self.set_nickname.clicked.connect(self.nickmake)

        # 스레드 동작
        cth = Thread(target=self.reception, args=(self.c,))
        cth.start()

    # 수신
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
                    # QMessageBox.warning(self, '안내창', '닉네임이 중복되었습니다.')
                    self.nickname_input.clear()
            elif r_msg[0] == '접속자':
                self.accessor_list.clear()
                for i in r_msg[1]:
                    self.accessor_list.addItem(f'{i[1]}[{i[0]}, {i[2]}]')

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

    def closeEvent(self, e):
        msg = ['나감', '']
        msg = json.dumps(msg)
        self.c.sendall(msg.encode())
        print('나감')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass(ip, port)
    myWindow.show()
    app.exec_()
