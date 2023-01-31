import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from socket import *
from threading import *

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

    def initialize_socket(self, sip, sport):
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((sip, sport))

    def roommake(self):
        print('아직')

    def nickmake(self):
        nick = self.nickname_input.text()
        if nick:
            self.nickname.setText(nick)
            self.nickname_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass(ip, port)
    myWindow.show()
    app.exec_()
