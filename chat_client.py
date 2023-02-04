import datetime
import faulthandler
import json
import socket
import sys
import threading
import time
from tkinter.simpledialog import askstring

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox, QWidget, QListWidget
from select import *
from socket import *
from tkinter import messagebox, Tk

qt_ui = uic.loadUiType('main_temp.ui')[0]
server_ip = '10.10.21.108'


class MainWindow(QWidget, qt_ui):

    # 초기 설정

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.Client.setCurrentIndex(0)

        self.thread_switch = 0
        self.constructor = ''

        self.chat_client = ''
        self.sock = ''
        self.socks = []

        self.BUFFER = 1024
        self.port = 9000
        self.invitation_preparation = False
        self.game_state = False
        self.subject.clear()

        self.welcome = QLabel(self)

        self.set_nickname.clicked.connect(self.check_nickname)
        self.make_room.clicked.connect(self.make_chat_room)
        self.room_list.clicked.connect(self.enter_chat_room_branch)
        self.exit.clicked.connect(self.go_main)

        self.nickname_input.returnPressed.connect(self.check_nickname)
        self.chat.returnPressed.connect(self.send_chat)

        # 채팅방 초대 목록을 참여자 목록으로 변경
        self.member.clicked.connect(self.click_member)
        # 채팅방 참여자 목록을 초대 목록으로 변경
        self.invite.clicked.connect(self.click_invite)
        # 게임시작 하기
        self.game_start.clicked.connect(self.start_game)

        # 스무고개 주제 정하기
        self.set_subject.returnPressed.connect(self.topic_selection)

        self.connect_to_main_server()

    # 메인 서버로 연결하는 스레드, 소켓 옵션 부여 등 기본 설정 후 get_message 함수 스레드로 동작
    def connect_to_main_server(self):
        self.set_socket()
        self.set_thread()

    def set_socket(self):
        self.sock = socket()
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socks.append(self.sock)

        try:
            self.sock.connect((server_ip, self.port))

        except ConnectionRefusedError:
            print('서버가 꺼져 있습니다. 프로그램을 종료합니다.')
            exit()

    def set_thread(self):
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
                            print(f'받은 메시지: {message} [{datetime.datetime.now()}]')
                            self.command_processor(message[0], message[1])

    def send_command(self, command, content):
        data = json.dumps([command, content], )
        print(f'보낸 메시지: {data} [{datetime.datetime.now()}]')
        self.sock.send(data.encode())

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
                self.fill_content_in_target(self.accessor_list, content)
                self.show_room_list()
            elif self.invitation_preparation:
                self.fill_content_in_target(self.member_list, content)
            elif not self.invitation_preparation:
                self.fill_content_in_target(self.member_list, content)

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

        elif command == '/print_chat':
            self.print_chat(content)

        elif command == '/refuse':
            self.refuse()

        elif command == '/show_user_list':
            self.show_user_list()

        elif command == '/understaffed':
            self.understaffed()

        elif command == '/presenter':
            self.presenter()

        elif command == '/entrant':
            self.entrant()

        elif command == '/topic':
            self.subject.setText(content)

        elif command == '/game_abnormal_stop':
            self.game_stop()

        elif command == '/load_chat_again':
            self.load_chat_again()

        else:
            pass

    """
    초기 설정 종료
    이하 GUI 스위치 커넥션
    """

    # 닉네임 설정 버튼 클릭 혹은 닉네임 입력창 엔터키
    # 닉네임 입력 체크을 체크함
    def check_nickname(self):
        # 닉네임 입력 칸이 비어있을 경우
        if self.nickname_input.text() == '':
            self.empty_nickname_warning()

        else:
            # 닉네임이 정상적으로 입력되었을 경우 서버에 닉네임 중복 확인 요청
            self.send_command('/check_nickname_exist', self.nickname_input.text())

    @staticmethod
    def empty_nickname_warning():
        # 스레드 작동중 PyQt를 이용해 새 창을 띄우면 프로그램이 터져 TKinter를 이용해 메세지 창 출력
        tk_window = Tk()
        # TKinter를 이용해 메세지 창을 출력하면 새 창이 함께 출력되기 때문에 새 창을 보이지 않는 곳으로 보냄
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo('닉네임 미입력', '닉네임을 입력하세요.')
        # 메세지 창 닫힐 시 TKinter 새 창도 닫음
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

    # 채팅방 이름 클릭
    # 채팅방 입장 확인을 받고 채팅방 입장 결정시 enter_chat_room 함수 호출
    def enter_chat_room_branch(self):
        reply = QMessageBox.question(self, '입장 확인', '채팅방에 입장 하시겠습니까?', QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.enter_chat_room()

        else:
            pass

    # 서버에 해당 채팅방의 포트를 요청
    def enter_chat_room(self):
        self.reset_member_button()
        self.constructor = self.room_list.currentItem().text().split('님의 방')[0]
        self.send_command('/request_port', self.constructor)

    # 채팅방에서 나가기 버튼 클릭
    # 메인 페이지로 되돌아감
    def go_main(self):
        self.reset_member_button()
        self.Client.setCurrentIndex(0)
        self.port = 9000
        self.reconnect_to_server()
        self.chat.clear()
        self.invitation_preparation = False

    # 소켓을 초기화한 후 메인 서버로 재연결
    def reconnect_to_server(self):
        self.reinitialize_socket()
        self.sock.connect((server_ip, self.port))

    def reinitialize_socket(self):
        self.deactivate_socket()
        self.activate_socket()

        self.thread_switch = 1

    def deactivate_socket(self):
        self.thread_switch = 0
        # 소켓 리스트에서 소켓 제거 후 소켓 닫음
        self.socks.remove(self.sock)
        self.sock.close()

    def activate_socket(self):
        # 소켓 재정의 및 리스트에 추가
        self.sock = socket()
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socks.append(self.sock)

    # 채팅창 엔터키 입력으로 발동
    # 서버로 채팅을 보냄
    def send_chat(self):
        chat_content = self.chat.text()
        self.send_command('/chat', chat_content)
        self.chat.clear()


    """
    GUI 스위치 커넥션 종료
    이하 명령문 송수신
    """

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
            self.nickname_not_set()

        # 닉네임 기록이 존재할 경우 닉네임 출력
        else:
            self.nickname_set(nickname)

        # 및 유저 리스트 출력함
        self.show_user_list()

    def nickname_not_set(self):
        self.welcome.setText('')
        self.nickname.setText('닉네임을 설정해주세요.')

    def nickname_set(self, nickname):
        self.nickname.setText(f'{nickname}')
        self.welcome.setText('님 환영합니다.')
        self.welcome.setGeometry(len(nickname) * 12 + 690, 9, 85, 16)

    # DB에서 현재 port가 9000(메인)인 유저들을 불러와서 accessor_list에 출력함
    def show_user_list(self):
        # 기존 접속자 리스트 초기화
        self.accessor_list.clear()
        self.send_command('/show_user', self.port)

    # /nickname_exisis 명령문
    # 닉네임 중복임을 알리는 알림창을 출력하고 닉네임 입력칸 클리어
    def nickname_exists(self):
        self.show_tk_messagebox('닉네임 중복', '이미 존재하는 닉네임입니다.')
        self.nickname_input.clear()

    @staticmethod
    def show_tk_messagebox(title, message):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo(title, message)
        tk_window.destroy()

    # /set_user_list 명령문
    # 서버로부터 전달받은 유저 목록을 유저 목록 창에 출력하고 서버에 채팅방 목록을 요청함
    @staticmethod
    def fill_content_in_target(target, login_user_list):
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
    def room_exists(self):
        self.show_tk_messagebox('생성 불가', '이미 생성된 방이 있습니다.')

    # /open_chat_room 명령문
    # 소켓 커넥션을 채팅방으로 변경하고 채팅방 페이지를 출력
    def open_chat_room(self, port):
        self.port = port
        self.send_command('/renew_room_list', '')
        time.sleep(1)
        self.reconnect_to_server()
        self.move_to_chat_room()

    # 환영 문구를 제거하고 위젯의 스택을 채팅방으로 옮김
    def move_to_chat_room(self):
        self.welcome.setText('')
        self.setup_chatroom()
        self.Client.setCurrentIndex(1)

    # 채팅 페이지 초기설정
    def setup_chatroom(self):
        # 채팅창 클리어
        self.chat_list.clear()
        self.send_command('/load_chat', self.port)

    def load_recent_chat(self, content):
        if content is not None:
            for i in range(len(content) - 1, -1, -1):
                print(f'[{content[i][0]}]{content[i][1]}{content[i][2]}')
                self.chat_list.addItem(f'[{content[i][0]}]{content[i][1]}{content[i][2]}')

        self.send_command('/show_user', self.port)

    def print_chat(self, content):
        self.chat_list.addItem(content)
        time.sleep(0.1)
        self.chat_list.scrollToBottom()

    def load_chat_again(self):
        self.send_command('/load_chat', self.port)

    # 초대장 알람
    def invite_user(self, nickname):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        reply = messagebox.askquestion('초대장', f'{nickname}님방 에서 초대장이 왔습니다. 입장하시겠습니까?')
        if reply == 'yes':
            self.reset_member_button()
            self.send_command('/request_port', nickname)
        else:
            self.send_command('/refuse', '')
        tk_window.destroy()

    def invite_user(self, nickname):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        reply = messagebox.askquestion('초대장', f'{nickname}님방 에서 초대장이 왔습니다. 입장하시겠습니까?')
        if reply == 'yes':
            self.reset_member_button()
            self.send_command('/request_port', nickname)
        else:
            self.send_command('/refuse', '')
        tk_window.destroy()

    # 채팅창에서 참가자 보기 버튼 눌렸을때
    def click_member(self):
        self.invitation_preparation = False
        self.show_member(self.port)
        self.member_button()

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
            self.member_button()

    # 참여자 보기 버튼 상태 초기화
    def reset_member_button(self):
        self.invitation_preparation = False
        self.member_button()

    # 버튼 숨기고 나타나게하기
    def member_button(self):
        if self.invitation_preparation:
            self.member.show()
            self.invite.setText('초대 하기')
        else:
            self.member.hide()
            self.invite.setText('초대 목록')

    # 채팅방 에서 초대가능 , 참가 인원 보여주기
    def show_member(self, port):
        if not self.invitation_preparation:
            self.send_command('/show_member', [f'{self.invitation_preparation}', port])
        else:
            self.send_command('/show_member', [f'{self.invitation_preparation}', port])

    # 초대하기
    def invitation(self, user):
        if not self.game_state:
            self.send_command('/invitation', [user, self.constructor])

    # 초대 거절 알림
    def refuse(self):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo('초대 결과', '거절하였습니다.')
        tk_window.destroy()

    # 게임 시작
    def start_game(self):
        self.send_command('/set_game', self.port)

    # 게임 참가 인원 부족 알람
    def understaffed(self):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo('인원 부족', '인원이 부족 합니다.')
        tk_window.destroy()

    # 주제 및 정답 정하기
    def topic_selection(self):
        topic = self.set_subject.text()
        if topic:
            self.set_subject.clear()
            self.subject.setText(topic)
            tk_window = Tk()
            tk_window.geometry("0x0+3000+6000")
            problem = askstring('안내창', '문제를 입력하세요')
            tk_window.destroy()
            self.send_command('/topic_selection', [topic, problem, self.port])

    # 출제자 선정
    def presenter(self):
        self.game_stack.setCurrentIndex(1)
        self.game_setting()

    # 참가자 선정
    def entrant(self):
        self.game_stack.setCurrentIndex(0)
        self.game_setting()

    # 게임 초기 셋팅
    def game_setting(self):
        self.game_state = True
        self.game_start.hide()
        self.exit.hide()
        self.question.hide()

    # 게임 비정상 종료
    def game_stop(self):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo('안내창', '인원이 나가 게임이 종료 되었습니다.')
        tk_window.destroy()
        self.game_end_set()

    # 게임 종료 셋팅
    def game_end_set(self):
        self.game_stack.setCurrentIndex(0)
        self.game_state = False
        self.game_start.show()
        self.exit.show()
        self.question.show()
        self.subject.clear()


if __name__ == '__main__':
    faulthandler.enable()
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()
