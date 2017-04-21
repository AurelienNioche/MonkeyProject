from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *

from graphics.generic import Colors


class Gauge(QWidget):

    def __init__(self, color="black"):

        super().__init__()

        self.background_color = "white"

        self.color = color
        self.token_number = 0

        self.create_background()

    def create_background(self):

        pal = QPalette()
        pal.setColor(QPalette.Background, getattr(Colors, self.background_color))
        self.setAutoFillBackground(True)
        self.setPalette(pal)

    def paintEvent(self, event):

        painter = QPainter()
        painter.begin(self)

        pen = QPen()
        brush = QBrush()

        # ----------- #

        line_width = int(1 / 60. * self.height())
        gauge_width = 0.25 * self.width()
        gauge_height = 0.9 * self.height()

        # ---------- #

        self.draw_gauge(line_width=line_width, gauge_width=gauge_width, gauge_height=gauge_height, painter=painter,
                        pen=pen)
        self.draw_tokens(line_width=line_width, gauge_width=gauge_width, gauge_height=gauge_height,
                         painter=painter, pen=pen, brush=brush)

        painter.end()

    def draw_gauge(self, line_width, gauge_width, gauge_height, painter, pen):

        pen.setColor(getattr(Colors, self.color))
        pen.setWidth(line_width)
        painter.setPen(pen)

        # ------------ #

        # Draw a rectangle
        rectangle = QRectF(
            self.width()/2. - gauge_width/2.,
            self.height()/2. - gauge_height/2.,
            gauge_width,
            gauge_height)

        painter.drawRect(rectangle)

        # ------------ #

        # Hide the top
        pen.setColor(QColor(255, 255, 255))
        pen.setWidth(1.1*line_width)
        painter.setPen(pen)

        painter.drawLine(
                self.width()/2. - gauge_width/2.,
                self.height()/2. - gauge_height/2.,
                self.width()/2. + gauge_width/2.,
                self.height()/2. - gauge_height/2.)

    def draw_tokens(self, line_width, gauge_width, gauge_height, painter, pen, brush):

        # ------------ #

        token_diameter = gauge_width - line_width*2

        first_token_position = \
            self.height()/2. + gauge_height/2. - token_diameter - line_width

        # ------------ #

        pen.setColor(getattr(Colors, self.color))
        pen.setWidth(line_width)
        painter.setPen(pen)

        brush.setColor(getattr(Colors, self.color))
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)

        # --------- #

        for i in range(self.token_number):

            rect = QRectF(
                self.width()/2. - token_diameter/2.,
                first_token_position - i*(token_diameter + line_width),
                token_diameter,
                token_diameter)

            painter.drawEllipse(rect)

        # ----------- #

    def set_quantity(self, quantity):

        self.token_number = int(quantity)

    def set_color(self, color):

        self.color = color