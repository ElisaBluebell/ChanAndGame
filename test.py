import pymysql as p
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic

form_class = uic.loadUiType("room.ui")[0]


class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.conn = p.connect(host='127.0.0.1', port=3306, user='root', password='0000', db='step6', charset='utf8')
        self.c = self.conn.cursor()
        self.conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()