import threading
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


class MultiChatServer:

    def __init__(self):

        self.clients = list()
        # 소켓 세팅
        self.s = socket(AF_INET, SOCK_STREAM)
        self.ip = '10.10.21.108'
        self.port = 9000
        self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.s.bind((self.ip, self.port))
        print('클라이언트 대기중...')
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
            # 닉네임 확인
            try:
                spl = f'select ip, 닉네임 from state;'
                c_ip = execute_db(spl)
                if c_ip[0][1] == '':
                    c.sendall('닉네임을 설정해주세요.'.encode())
            except:
                spl = f"insert into state values('{ip}','','9000');"
                execute_db(spl)
                c.sendall('닉네임을 설정해주세요.'.encode())

            else:
                c.sendall(str(c_ip[0][1]).encode())

            cth = Thread(target=self.handler, args=(c, ip))
            cth.start()

    # 이벤트 확인
    def handler(self, c, ip):
        while True:
            r_msg = c.recv(1024)
            r_msg = json.loads(r_msg.decode())
            if r_msg[0] == '닉네임':
                self.set_nickname(c, ip, r_msg[1])

    # 클라에서 닉네임 설정 버튼을 누르면 중복확인 및 DB에 닉네임 저장
    def set_nickname(self, c, ip, r_msg):
        overlap = False
        sql = f"select 닉네임 from state;"
        nick = execute_db(sql)
        for name in nick:
            if r_msg in name:
                overlap = False
                break
            else:
                overlap = True
        if overlap:
            sql = f"update state set 닉네임 = '{r_msg}' where ip = '{ip}';"
            execute_db(sql)
            c.sendall('True'.encode())
        else:
            c.sendall('False'.encode())


if __name__ == '__main__':
    MultiChatServer()


