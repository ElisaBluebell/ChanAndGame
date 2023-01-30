from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

room_ui = uic.loadUiType('room.ui')[0]


class ChatClient(QWidget, room_ui):
    def __init__(self):
        super().__init__()
