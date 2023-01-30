from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow

room_ui = uic.loadUiType('room.ui')[0]


class ChatClient(QMainWindow, room_ui):
    def __init__(self):
        super().__init__()
