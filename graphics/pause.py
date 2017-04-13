from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from graphics.generic import Colors


class Pause(QWidget):

    def __init__(self):
        super().__init__()

        self.background_color = "white"
        self.create_background()

    def create_background(self):

        pal = QPalette()
        pal.setColor(QPalette.Background, getattr(Colors, self.background_color))
        self.setAutoFillBackground(True)
        self.setPalette(pal)

    def paintEvent(self, e):

        painter = QPainter()
        painter.begin(self)

        pen = QPen()
        brush = QBrush()

        # --------------- #

        line_width = int(1 / 60. * self.height())
        rectangle_width = 0.1 * self.width()
        rectangle_height = 0.35 * self.height()
        margin = 0.03 * self.width()

        # --------------- #

        pen.setColor(getattr(Colors, "white"))
        painter.setPen(pen)
        brush.setColor(getattr(Colors, "white"))
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)

        # --------------- #

        rectangle = QRectF(
            0,
            0,
            self.width(),
            self.height())

        painter.drawRect(rectangle)

        # --------------- #

        pen.setColor(QColor(220, 220, 220))  # Grey
        pen.setWidth(line_width)
        painter.setPen(pen)

        # --------------- #

        rect_y = self.height() / 2. + margin/2. - rectangle_height/2.

        x_center = self.width() / 2.

        rectangle = QRectF(
            x_center + margin/2.,
            rect_y,
            rectangle_width,
            rectangle_height)

        painter.drawRect(rectangle)

        # --------------- #

        rectangle = QRectF(
            x_center - margin / 2. - rectangle_width,
            rect_y,
            rectangle_width,
            rectangle_height)

        painter.drawRect(rectangle)

        # ------------- #

        painter.end()