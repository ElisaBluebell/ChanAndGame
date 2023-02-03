import faulthandler
import json
import socket
import sys
import threading
import time

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox, QWidget
from select import *
from socket import *
from tkinter import messagebox, Tk

qt_ui = uic.loadUiType('main_temp.ui')[0]
my_ip = gethostbyname(gethostname())


class MainWindow(QWidget, qt_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.Client.setCurrentIndex(0)
        self.welcome = QLabel(self)
        self.thread_switch = 0

        self.chat_client = ''
        self.sock = socket()
        self.socks = []
        self.BUFFER = 1024
        self.port = 9000
        self.invitation_preparation = False
        self.member.hide()

        self.set_nickname.clicked.connect(self.check_nickname)
        self.make_room.clicked.connect(self.make_chat_room)
        self.room_list.clicked.connect(self.enter_chat_room)
        self.exit.clicked.connect(self.go_main)
        self.member.clicked.connect(self.click_member)
        self.invite.clicked.connect(self.click_invite)

        self.nickname_input.returnPressed.connect(self.check_nickname)
        self.chat.returnPressed.connect(self.send_chat)

        self.connect_to_main_server()

    # 메인 서버로 연결하는 스레드, 소켓 옵션 부여 등 기본 설정 후 get_message 함수 스레드로 동작
    def connect_to_main_server(self):
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        self.socks.append(self.sock)
        self.sock.connect((my_ip, self.port))
        self.thread_switch = 1

        get_message = threading.Thread(target=self.get_message, daemon=True)
        get_message.start()

    # 수신한 메시지를 원래 형태로 복원하여 명령 부분으로 전송
    def get_message(self):
        while True:
            if self.thread_switch == 1:
                r_sock, dummy1, dummy2 = select(self.socks, [], [], 0)
                if r_sock:
                    for s in r_sock:
                        if s == self.sock:
                            message = eval(self.sock.recv(self.BUFFER).decode())
                            print(f'받은 메시지: {message}')
                            self.command_processor(message[0], message[1])

    def send_command(self, command, content):
        data = json.dumps([command, content])
        self.sock.send(data.encode())

    # 초기 설정 종료

    # 이하 명령문 송수신

    # 명령문 커넥트
    def command_processor(self, command, content):
        if command == '/setup_nickname':
            self.setup_nickname()

        elif command == '/set_nickname_complete':
            self.show_nickname(content)

        elif command == '/nickname_exists':
            self.nickname_exists()

        elif command == '/set_user_list':
            if self.Client.currentIndex() == 0:
                self.set_user_list(self.accessor_list, content)
                self.show_room_list()
            elif self.invitation_preparation:
                self.set_user_list(self.member_list, content)
            elif not self.invitation_preparation:
                self.set_user_list(self.member_list, content)
            # else:
            #     self.set_user_list(self.member_list, content)
            #     print(self.member_list)

        elif command == '/set_room_list':
            self.set_room_list(content)

        elif command == '/room_already_exists':
            self.room_exists()

        elif command == '/open_chat_room':
            self.open_chat_room(content)

        elif command == '/load_recent_chat':
            self.load_recent_chat(content)

        elif command == '/invitation':
            self.invite_user(content)

    # /setup_nickname 명령문
    # 서버에 닉네임 설정 프로세스를 요청을 보내고 닉네임 입력창을 클리어
    def setup_nickname(self):
        self.send_command('/setup_nickname', self.nickname_input.text())
        self.nickname_input.clear()

    # /show_nickname 명령문
    # 전달받은 닉네임을 메인 화면에 출력
    def show_nickname(self, nickname):
        # 해당 IP로 이전에 닉네임을 설정한 기록이 없을 경우 닉네임을 전달받지 못함. 닉네임 설정 메시지 출력
        if not nickname:
            self.welcome.setText('')
            self.nickname.setText('닉네임을 설정해주세요.')

        # 닉네임 기록이 존재할 경우 닉네임 출력
        else:
            self.nickname.setText(f'{nickname}')
            self.welcome.setText('님 환영합니다.')
            self.welcome.setGeometry(len(nickname) * 12 + 690, 9, 85, 16)
        # 및 유저 리스트 출력함
        self.show_user_list()

    # DB에서 현재 port가 9000(메인)인 유저들을 불러와서 accessor_list에 출력함
    def show_user_list(self):
        # 기존 접속자 리스트 초기화
        self.accessor_list.clear()
        self.member_list.clear()
        self.send_command('/show_user', self.port)

    # 닉네임 입력 체크
    def check_nickname(self):
        # 닉네임 입력 칸이 비어있을 경우
        if self.nickname_input.text() == '':
            # 스레드 작동중 PyQt를 이용해 새 창을 띄우면 프로그램이 터져 TKinter를 이용해 메세지 창 출력
            tk_window = Tk()
            # TKinter를 이용해 메세지 창을 출력하면 새 창이 함께 출력되기 때문에 새 창을 보이지 않는 곳으로 보냄
            tk_window.geometry("0x0+3000+6000")
            messagebox.showinfo('닉네임 미입력', '닉네임을 입력하세요.')
            # 메세지 창 닫힐 시 TKinter 새 창도 닫음
            tk_window.destroy()

        else:
            # 닉네임이 정상적으로 입력되었을 경우 서버에 닉네임 중복 확인 요청
            self.send_command('/check_nickname_exist', self.nickname_input.text())

    # /nickname_exisis 명령문
    # 닉네임 중복임을 알리는 알림창을 출력하고 닉네임 입력칸 클리어
    def nickname_exists(self):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo('닉네임 중복', '이미 존재하는 닉네임입니다.')
        tk_window.destroy()

        self.nickname_input.clear()

    # /set_user_list 명령문
    # 서버로부터 전달받은 유저 목록을 유저 목록 창에 출력하고 서버에 채팅방 목록을 요청함
    def set_user_list(self, target, login_user_list):
        target.clear()
        for i in range(len(login_user_list)):
            target.insertItem(i, login_user_list[i])

    # 채팅방 목록을 초기화하고 서버에 채팅방 목록을 요청하는 명령문 전송
    def show_room_list(self):
        self.room_list.clear()
        self.send_command('/get_room_list', '')

    # /set_room_list 명령문
    # 서버로부터 전달받은 채팅방 목록을 채팅방 목록 창에 출력함
    def set_room_list(self, room_list):
        for i in range(len(room_list)):
            self.room_list.insertItem(i, f'{room_list[i][1]}님의 방')

    # /room_exists 명령문
    # 유저가 이미 채팅방을 개설했을 경우 서버로부터 해당 정보를 전달받아 알림창 출력
    @staticmethod
    def room_exists():
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo('생성 불가', '이미 생성된 방이 있습니다.')
        tk_window.destroy()

    # 방 만들기 버튼 클릭
    # 닉네임 설정 유무를 확인한 뒤 서버에 채팅창 생성을 요청
    def make_chat_room(self):
        if not self.no_nickname():
            self.send_command('/make_chat_room', f'{self.nickname.text()}')

    # 닉네임 설정 여부를 판별하여 닉네임이 설정되지 않은 상태에서 채팅방 개설 시도시 생성 요청 알림창 출력 
    def no_nickname(self):
        if self.nickname.text() == '닉네임을 설정해주세요.':
            QMessageBox.warning(self, '닉네임 설정', '닉네임 설정이 필요합니다.')
            return 1

        return 0

    # /open_chat_room 명령문
    # 소켓 커넥션을 채팅방으로 변경하고 채팅방 페이지를 출력
    def open_chat_room(self, port):
        self.port = port
        self.connect_to_chat_room()
        self.move_to_chat_room()

    # 서버와 연결된 소켓 정보를 초기화한 뒤 서버로부터 전달받은 채팅방 포트로 재연결
    def connect_to_chat_room(self):
        self.reinitialize_socket()
        self.sock.connect((my_ip, self.port))

    def reinitialize_socket(self):
        self.thread_switch = 0
        # 소켓 리스트에서 소켓 제거 후 소켓 닫음
        self.socks.remove(self.sock)
        self.sock.close()
        
        # 소켓 재정의 및 리스트에 추가
        self.sock = socket()
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socks.append(self.sock)

        self.thread_switch = 1
        
    # 환영 문구를 제거하고 위젯의 스택을 채팅방으로 옮김
    def move_to_chat_room(self):
        self.welcome.setText('')
        self.setup_chatroom()
        self.Client.setCurrentIndex(1)

    # 채팅방 이름 더블클릭
    # 채팅방 입장 확인을 받고 채팅방 입장 결정시 서버에 해당 채팅방의 포트를 요청
    def enter_chat_room(self):
        reply = QMessageBox.question(self, '입장 확인', '채팅방에 입장 하시겠습니까?', QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            nickname = self.room_list.currentItem().text().split('님의 방')[0]
            self.send_command('/request_port', nickname)

        else:
            pass

    # 채팅 페이지 초기설정
    def setup_chatroom(self):
        # 채팅창 클리어
        self.chat_list.clear()
        self.send_command('/show_user', self.port)
        time.sleep(0.2)
        self.send_command('/load_chat', self.port)

    def load_recent_chat(self, content):
        row = 1

        if content is not None:
            for i in range(len(content)):
                self.chat_list.insertItem(row, f'[{content[i][0][11:-3]}]{content[i][1]}{content[i][2]}')
                row += 1

    def invite_user(self, port):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo('초대', f'{port}방 에서 초대장이 왔습니다.')
        tk_window.destroy()

    def receive_chat(self):
        pass

    def send_chat(self):
        chat_content = self.chat.text()
        self.send_command('/chat', chat_content)
        self.chat.clear()

    def go_main(self):
        self.Client.setCurrentIndex(0)
        self.connect_to_main()
        self.chat.clear()
        self.invitation_preparation = False

    def connect_to_main(self):
        self.reinitialize_socket()
        self.port = 9000
        self.sock.connect((my_ip, self.port))

    # 채팅창에서 참가자보기 버튼 눌렸을때
    def click_member(self):
        self.invitation_preparation = False
        self.show_member(self.port)
        self.member.hide()

    # 채팅창에서 초대하기 버튼 눌렸을때 대기창 인원 보여주기 및 초대하기
    def click_invite(self):
        if self.invitation_preparation:
            try:
                member = self.member_list.currentItem().text()
                self.invitation(member)
            except:
                pass
        else:
            self.invitation_preparation = True
            self.show_member(self.port)
            self.member.show()

    # 하는중
    def show_member(self, port):
        if not self.invitation_preparation:
            self.send_command('/show_member', [f'{self.invitation_preparation}', port])
        else:
            self.send_command('/show_member', [f'{self.invitation_preparation}', port])

    def invitation(self, user):
        self.send_command('/invitation', [user, self.port])


if __name__ == '__main__':
    faulthandler.enable()
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()
