from socket import *
from threading import *
import pymysql as p
import json

chost = '127.0.0.1'
cport = 3306
cuser = 'root'
cpw = '0000'
cdb = 'chatandgame'


def execute_db(sql):
    conn = p.connect(host=chost, port=cport, user=cuser, password=cpw, db=cdb, charset='utf8')
    c = conn.cursor()
    # 인수로 받아온 쿼리문에 해당하는 작업 수행
    c.execute(sql)
    # 커밋
    conn.commit()
    conn.close()
    # 결과 반환
    return c.fetchall()


class MainServer:

    def __init__(self):

        self.clients = list()
        # 소켓 세팅
        self.s = socket(AF_INET, SOCK_STREAM)
        self.ip = '10.10.21.108'
        self.port = 9000
        self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.s.bind((self.ip, self.port))
        self.s.listen(100)
        self.accept_client()

    # 클라 접속시 state DB 에 저장 및 초기화
    def accept_client(self):
        while True:
            # 클라 소켓 생성 및 클라 ip,port 받기
            client = c, (ip, port) = self.s.accept()
            if client not in self.clients:
                self.clients.append(client)
            print(f'{ip} : {port} 가 연결되었습니다.')

            # 클라 접속시 DB의 port를 9000(대기방)으로 변경
            try:
                sql = f'update state set port ="9000" where ip = "{ip}";'
                execute_db(sql)
            except:
                pass

            # 닉네임 확인
            try:
                sql = f'select ip, 닉네임 from state where ip = "{ip}";'
                c_ip = execute_db(sql)

                if c_ip[0][1] == '':
                    msg = json.dumps(['초기닉네임', '닉네임을 설정해주세요.'])
            except:
                sql = f"insert into state values('{ip}','','9000');"
                execute_db(sql)
                msg = json.dumps(['초기닉네임', '닉네임을 설정해주세요.'])

            else:
                msg = json.dumps(['초기닉네임', str(c_ip[0][1])])

            c.sendall(msg.encode())
            self.show_list()

            # 스레드 동작
            cth = Thread(target=self.reception, args=(c, ip), daemon=True)
            cth.start()

    # 수신
    def reception(self, c, ip):
        while True:
            self.show_list()
            r_msg = c.recv(1024)
            r_msg = json.loads(r_msg.decode())
            print('main server', r_msg)
            if r_msg[0] == '나감':
                sql = f'update state set port ="0" where ip = "{ip}";'
                execute_db(sql)
                c.close()
                print(f'{ip} 연결 종료')
                break
            elif r_msg[0] == '닉네임':
                self.set_nickname(c, ip, r_msg)
            elif r_msg[0] == '방만들기':
                self.room_confirm(c, ip)
            elif r_msg[0] == '방이동':
                self.move_room(c, ip, r_msg)
            else:
                pass
        print(f'{ip} 연결 종료')

    def move_room(self, c, ip, r_msg):
        sql = f"select distinct port from chat where 방번호 = '{r_msg[1]}'"
        port = execute_db(sql)[0][0]
        sql = f"update state set port= '{port}' where ip = '{ip}';"
        execute_db(sql)
        msg = json.dumps([r_msg[0], port])
        c.sendall(msg.encode())
        ChatServer(port)

    def room_confirm(self, c, ip):
        sql = f'SELECT DISTINCT 방번호, 생성자 FROM chat where 생성자 = "{ip}";'
        con = execute_db(sql)
        if not con:
            num = self.room_number()
            port = self.port_number()
            sql = f"select 닉네임 from state where ip ='{ip}';"
            name = execute_db(sql)[0][0]
            sql = f"insert into chat values ({num}, '{name}', now(), '님이 채팅방을 생성하였습니다.', '{ip}','{port}' )"
            execute_db(sql)
            sql = f"update state set port= '{port}' where ip = '{ip}';"
            execute_db(sql)
            msg = json.dumps(['방생성', 'True', port])
            c.sendall(msg.encode())
            ChatServer(port)
        else:
            msg = json.dumps(['방생성', 'False'])
            c.sendall(msg.encode())

    def room_number(self):
        sql = f"select distinct 방번호 from chat;"
        room = execute_db(sql)
        roomnum = 0
        while True:
            roomnum += 1
            for i in room:
                if roomnum in i:
                    continue
                else:
                    return roomnum

    def port_number(self):
        sql = f"select distinct port from chat;"
        port = execute_db(sql)
        portnum = 9000
        while True:
            portnum += 1
            for i in port:
                if portnum in i:
                    continue
                else:
                    return portnum

    # 대기창에서 접속자, 방목로 보여주기
    def show_list(self):
        sql = 'select * from state where port != "0";'
        acc = execute_db(sql)
        sql = 'SELECT DISTINCT 방번호, 생성자 FROM chat;'
        room = execute_db(sql)
        for client in self.clients:
            s, (ip, port) = client
            msg = json.dumps(['목록', acc, room])
            try:
                s.sendall(msg.encode())
            except:
                pass

    # 클라에서 닉네임 설정 버튼을 누르면 중복확인 및 DB에 닉네임 저장
    def set_nickname(self, c, ip, r_msg):
        overlap = False
        sql = f"select 닉네임 from state;"
        nick = execute_db(sql)
        for name in nick:
            if r_msg[1] in name:
                overlap = False
                break
            else:
                overlap = True
        if overlap:
            sql = f"update state set 닉네임 = '{r_msg[1]}' where ip = '{ip}';"
            execute_db(sql)
            msg = json.dumps([r_msg, 'True'])
            c.sendall(msg.encode())
        else:
            msg = json.dumps([r_msg, 'False'])
            c.sendall(msg.encode())


class ChatServer:
    def __init__(self, port):

        self.clients = list()
        # 소켓 세팅
        self.s = socket(AF_INET, SOCK_STREAM)
        self.ip = '10.10.21.108'
        self.port = port
        self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.s.bind((self.ip, self.port))
        print(f'{port}방 입장 대기중...')
        self.s.listen(5)
        self.accept_client()

    def accept_client(self):
        while True:
            # 클라 소켓 생성 및 클라 ip,port 받기
            client = c, (ip, port) = self.s.accept()
            if client not in self.clients:
                self.clients.append(client)
            print(f'{self.port}방에 {ip} : {port} 가 연결되었습니다.')

            cth = Thread(target=self.reception, args=(c, ip), daemon=True)
            cth.start()

    def reception(self, c, ip):
        self.show_member()
        while True:
            try:
                r_msg = c.recv(1024)
                r_msg = json.loads(r_msg.decode())
                print('sub server', r_msg)
            except:
                break
            if r_msg[0] == '나감':
                sql = f'update state set port ="0" where ip = "{ip}";'
                execute_db(sql)
                c.close()
                self.show_member()
                print(f'{ip} 연결 종료')
                break
            elif r_msg[0] == '목록':
                self.member_check(c)
            elif r_msg[0] == '초대목록':
                self.guest_check(c)

    def guest_check(self, c):
        sql = f'select * from state where port !="{self.port}" and port !=0;'
        member = execute_db(sql)
        print(member)
        msg = json.dumps(['초대목록', member])
        c.sendall(msg.encode())

    def show_member(self):
        sql = f'select * from state where port ="{self.port}";'
        member = execute_db(sql)
        for client in self.clients:
            s, (ip, port) = client
            msg = json.dumps(['목록', member])
            try:
                s.sendall(msg.encode())
            except:
                pass

    def member_check(self, c):
        sql = f'select * from state where port ="{self.port}";'
        member = execute_db(sql)
        msg = json.dumps(['목록', member])
        c.sendall(msg.encode())



if __name__ == '__main__':
    MainServer()
