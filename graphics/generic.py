from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class Communicant(QObject):
    signal = pyqtSignal()


class Colors:

    white = QColor(255, 255, 255)
    black = QColor(0, 0, 0)
    blue = QColor(114, 212, 247)
    grey = QColor(220, 220, 220)
    green = QColor(18, 247, 41)
    red = QColor(255, 0, 0)


class Frame(QWidget):

    def __init__(self, background_color):

        super().__init__()

        self.background_color = background_color
        self.create_background()

    def create_background(self):

        pal = QPalette()
        pal.setColor(QPalette.Background, getattr(Colors, self.background_color))
        self.setAutoFillBackground(True)
        self.setPalette(pal)
