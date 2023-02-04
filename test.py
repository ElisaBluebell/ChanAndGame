import faulthandler
import json
from tkinter import messagebox, Tk

import pymysql
import socket
import sys
import threading

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox, QWidget
from select import *
from socket import *

qt_ui = uic.loadUiType('main_temp.ui')[0]


class MainWindow(QWidget, qt_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.Client.setCurrentIndex(0)
        self.welcome = QLabel(self)

        self.chat_client = ''
        self.sock = socket()
        self.chat_sock = socket()
        self.socks = []
        self.BUFFER = 1024

        self.set_nickname.clicked.connect(self.check_nickname)
        self.nickname_input.returnPressed.connect(self.check_nickname)
        self.make_room.clicked.connect(self.make_chat_room)
        self.room_list.clicked.connect(self.enter_chat_room)

        self.connect_to_main_server()

    def connect_to_main_server(self):
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        self.socks.append(self.sock)
        self.sock.connect(('10.10.21.121', 9000))

        get_message = threading.Thread(target=self.get_message, daemon=True)
        get_message.start()

    def get_message(self):
        while True:
            r_sock, w_sock, e_sock = select(self.socks, [], [], 0)
            if r_sock:
                for s in r_sock:
                    if s == self.sock:
                        message = eval(self.sock.recv(self.BUFFER).decode())
                        print(f'받은 메시지: {message}')
                        self.command_processor(message[0], message[1])

    def command_processor(self, command, content):
        if command == '/set_nickname_complete' or command == '/set_nickname_label':
            self.show_nickname(content)

        elif command == '/nickname_exists':
            self.nickname_exists()

        elif command == '/setup_nickname':
            self.setup_nickname()

        elif command == '/set_user_list':
            self.set_user_list(content)

        elif command == '/set_room_list':
            self.set_room_list(content)

        elif command == '/room_already_exists':
            self.room_exists()

        elif command == '/open_chat_room':
            self.open_chat_room(content)

    def check_nickname(self):
        if self.nickname_input.text() == '':
            tk_window = Tk()
            tk_window.geometry("0x0+3000+6000")
            messagebox.showinfo('닉네임 미입력', '닉네임을 입력하세요.')
            tk_window.destroy()

        else:
            self.check_nickname_exist()

    def check_nickname_exist(self):
        data = json.dumps(['/check_nickname_exist', self.nickname_input.text()])
        self.sock.send(data.encode())

    def setup_nickname(self):
        data = json.dumps(['/setup_nickname', self.nickname_input.text()])
        self.sock.send(data.encode())

        self.nickname_input.clear()

    def nickname_exists(self):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo('닉네임 중복', '이미 존재하는 닉네임입니다.')
        tk_window.destroy()

        self.nickname_input.clear()

    # DB에서 현재 port가 9000(메인화면이라고 가정)인 유저들을 불러와서 accessor_list에 출력함
    def show_user_list(self):
        self.accessor_list.clear()
        data = json.dumps(['/get_main_user_list', ''])
        self.sock.send(data.encode())

    def set_user_list(self, login_user_list):
        for i in range(len(login_user_list)):
            self.accessor_list.insertItem(i, login_user_list[i])

        self.show_room_list()

    def show_room_list(self):
        self.room_list.clear()
        data = json.dumps(['/get_room_list', ''])
        self.sock.send(data.encode())

    def set_room_list(self, room_list):
        for i in range(len(room_list)):
            self.room_list.insertItem(i, f'{room_list[i][1]}님의 방')

    def show_nickname(self, nickname):
        if not nickname:
            self.welcome.setText('')
            self.nickname.setText('닉네임을 설정해주세요.')

        else:
            self.nickname.setText(f'{nickname}')
            self.welcome.setText('님 환영합니다.')
            self.welcome.setGeometry(len(nickname) * 12 + 690, 9, 85, 16)

        self.show_user_list()

    def make_chat_room(self):
        if not self.no_nickname():
            data = json.dumps(['/make_chat_room', ''])
            self.sock.send(data.encode())

    def no_nickname(self):
        if self.nickname.text() == '닉네임을 설정해주세요.':
            QMessageBox.warning(self, '닉네임 설정', '닉네임 설정이 필요합니다.')
            return 1
        return 0

    def room_exists(self):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo('생성 불가', '이미 생성된 방이 있습니다.')
        tk_window.destroy()

    def open_chat_room(self, port):
        self.move_to_chat_room()
        self.show_room_list()

    def enter_chat_room(self):
        reply = QMessageBox.question(self, '입장 확인', '채팅방에 입장 하시겠습니까?', QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            user_name = self.room_list.currentItem().text().split('님의 방')[0]
            # 아직 IP로 표시되기 때문에 유저명이 아닌 IP를 일단 불러옴
            sql = f'SELECT port FROM chat WHERE 닉네임="{user_name}";'
            self.connect_to_chat_room()
            self.move_to_chat_room()

        else:
            pass

    def move_to_chat_room(self):
        self.Client.setCurrentIndex(1)
        self.welcome.setText('')

    def connect_to_chat_room(self):
        self.chat_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socks.append(self.chat_sock)


        self.chat_sock.connect(('10.10.21.121', 9001))

        get_message = threading.Thread(target=self.get_message, daemon=True)
        get_message.start()
        print("성공")

    def setup_chatroom(self):
        self.chat_list.clear()
        self.show_user()
        self.load_chat()

    def load_chat(self):
        self.room_create_info()
        self.insert_recent_chat()

    def room_create_info(self):
        # 통신 미적용으로 인해 임의로 9001번 포트 줌
        sql = 'SELECT * FROM chat WHERE port=9001 LIMIT 5;'
        chat_log = execute_db(sql)
        self.chat_list.insertItem(0, f'[{chat_log[0][2][:-3]}]{chat_log[0][1]}{chat_log[0][3]}')

    def insert_recent_chat(self):
        row = 1
        temp = None

        try:
            sql = 'SELECT * FROM chat WHERE port=9001 ORDER BY 시간 DESC LIMIT 21;'
            temp = execute_db(sql)
        except:
            pass
        if temp is not None:
            for i in range(len(temp), 1, -1):
                self.chat_list.insertItem(row, f'[{temp[i - 1][2][5:-3]}]{temp[i - 1][1]}: {temp[i - 1][3]}')
                row += 1
        self.chat_list.clicked.connect(self.printa)

    def printa(self):
        # chat_list = QListWidget
        print(self.chat_list.currentItem().text())

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
    faulthandler.enable()
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()
