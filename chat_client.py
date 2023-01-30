import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow

room_ui = uic.loadUiType('room.ui')[0]
qt_ui = uic.loadUiType('main.ui')[0]


class MainWindow(QMainWindow, qt_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.chat_client = ChatClient()


class ChatClient(QMainWindow, room_ui):
    def __init__(self):
        super().__init__()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()
