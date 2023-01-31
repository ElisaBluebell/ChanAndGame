from socket import *
from threading import *
import pymysql as p

chost = '127.0.0.1'
cport = 3306
cuser = 'root'
cpw = '0000'
cdb = 'chatandgame'


class MultiChatServer:

    def __init__(self):

        # db 연결
        self.conn = p.connect(host=chost, port=cport, user=cuser, password=cpw, db=cdb, charset='utf8')
        self.c = self.conn.cursor()
        self.conn.close()

        self.clients = list()
        self.mes = str()
        self.s = socket(AF_INET, SOCK_STREAM)
        self.ip = '10.10.21.108'
        self.port = 9000
        self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.s.bind((self.ip, self.port))
        print('클라이언트 대기중...')
        self.s.listen(100)
        self.accept_client()

    def open_db(self):
        self.conn = p.connect(host=chost, port=cport, user=cuser, password=cpw, db=cdb, charset='utf8')
        self.c = self.conn.cursor()

    def accept_client(self):
        while True:
            client = c, (ip, port) = self.s.accept()
            if client not in self.clients:
                self.clients.append(client)
            print(f'{ip} : {port} 가 연결되었습니다.')

    def closeEvent(self, e):
        self.open_db()
        self.c.execute('delete from state;')
        self.conn.commit()
        self.c.close()


if __name__ == '__main__':
    MultiChatServer()


