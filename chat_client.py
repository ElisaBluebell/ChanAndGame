import datetime
import faulthandler
import json
from tkinter import messagebox, Tk

import pymysql
import socket
import sys
import threading

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox
from select import *
from socket import *

room_ui = uic.loadUiType('room.ui')[0]
qt_ui = uic.loadUiType('main.ui')[0]


class MainWindow(QMainWindow, qt_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.welcome = QLabel(self)

        self.chat_client = ''
        self.sock = socket()
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
            self.room_list.insertItem(i, f'[{room_list[i][0]}번] {room_list[i][1]}님의 방')

    def show_nickname(self, nickname):
        if not nickname:
            self.welcome.setText('')
            self.nickname.setText('닉네임을 설정해주세요.')

        else:
            self.nickname.setText(f'{nickname}')
            self.welcome.setText('님 환영합니다.')
            self.welcome.setGeometry(len(nickname) * 12 + 710, 10, 85, 16)

        self.show_user_list()

    def make_chat_room(self):
        if self.check_have_room() == 1:
            QMessageBox.information(self, '생성 불가', '이미 생성된 방이 있습니다.')

        else:
            # 빈 방 체크
            empty_room_number = self.empty_number_checker('방번호', 1, 100)
            empty_port = self.empty_number_checker('port', 9001, 9100)

            sql = f'''INSERT INTO chat VALUES ({empty_room_number}, "{self.nickname.text()}", 
            "{str(datetime.datetime.now())[:-7]}", "님이 채팅방을 생성하였습니다.", 
            "{socket.gethostbyname(socket.gethostname())}", "{empty_port}");'''
            execute_db(sql)

            self.chat_client = ChatClient()
            self.chat_client.show()
            self.show_room_list()

    # 빈 숫자 확인을 위한 함수, 매개변수(칼럼명, 시작값, 종료값)
    def empty_number_checker(self, item, start, end):
        sql = f'SELECT {item} FROM chat;'
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

    # 방 개설 여부 확인
    def check_have_room(self):
        # 생성자 IP 정보를 DB에서 받아와서 현재 접속 IP와 대조함, 일치시 1, 일치하는 값 없을 시 0 반환
        sql = f'''SELECT 닉네임 FROM chat;'''
        temp = execute_db(sql)

        for room_maker in temp:
            if self.nickname.text() == room_maker[0]:
                return 1
        return 0

    def enter_chat_room(self):
        reply = QMessageBox.question(self, '입장 확인', '채팅방에 입장 하시겠습니까?', QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            user_name = self.room_list.currentItem().text().split('님의 방')[0]
            # 아직 IP로 표시되기 때문에 유저명이 아닌 IP를 일단 불러옴
            sql = f'SELECT port FROM chat WHERE 생성자="{user_name}";'
            port = execute_db(sql)[0][0]
            self.chat_client = ChatClient()
            self.chat_client.show()

        else:
            pass


class ChatClient(QMainWindow, room_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setup_chatroom()

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
