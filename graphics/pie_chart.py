from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np

from graphics.generic import Colors


class PieChart(QWidget):

    def __init__(self, textures_folder, position):

        super().__init__()

        self.textures_folder = textures_folder
        self.position = position

        self.background_color = "white"

        self.quantity_possibilities = np.arange(-4, 5, 1)

        self.quantities = [0, 0]

        self.p = 0
        self.beginning_angle = 0

        self.ellipse = None

        self.display = 1

        self.textures = {}

        self.load_textures()

        self.create_background()

    def create_background(self):

        pal = QPalette()
        pal.setColor(QPalette.Background, getattr(Colors, self.background_color))
        self.setAutoFillBackground(True)
        self.setPalette(pal)

# ------------------------------------------------ TEXTURES ------------------------------------------------ #

    def load_textures(self):

        for i in self.quantity_possibilities:

            self.textures[i] = QImage("{}/gain{}.png".format(self.textures_folder, i))

# ------------------------------------------------ DRAW ------------------------------------------------ #

    def paintEvent(self, event):

        if self.display == 1:

            painter = QPainter()
            painter.begin(self)

            brush = QBrush()
            pen = QPen()

            # ------------ #

            c_diameter = 0.5 * self.height()
            line_width = int(1 / 60. * self.height())

            # ------------- #

            pen.setColor(Colors.black)
            pen.setWidth(line_width)
            painter.setPen(pen)

            # -------------- #

            rectangle = \
                QRectF(self.width()/2. - c_diameter/2.,
                       self.height()/2. - c_diameter/2.,
                       c_diameter,
                       c_diameter)

            ps = [self.p, 1-self.p]
            angles = [p*360*16 for p in ps]

            set_angle = self.beginning_angle*16

            for i in range(len(ps)):
                if ps[i] != 0:

                    if self.quantities[i] is not None:

                        # -------- #

                        brush.setTexture(
                            QPixmap(self.textures[self.quantities[i]].scaled(self.width()*2, self.height()*2,
                                                                             Qt.KeepAspectRatio,
                                                                             Qt.SmoothTransformation)))
                        brush.setStyle(Qt.TexturePattern)
                        painter.setBrush(brush)

                        # ---------- #

                        if angles[i] != 360*16:

                            painter.drawPie(rectangle, set_angle, angles[i])
                            set_angle += angles[i]

                        else:

                            painter.drawEllipse(rectangle)
                    else:
                        set_angle += angles[i]

            self.ellipse = QGraphicsEllipseItem(rectangle)

            # self.ellipse.setBrush(self.brush["transparent"])
            brush.setStyle(Qt.NoBrush)
            pen.setStyle(Qt.NoPen)
            self.ellipse.setBrush(brush)
            self.ellipse.setPen(pen)
            self.ellipse.paint(painter, QStyleOptionGraphicsItem())

            painter.end()

        else:
            pass

# ------------------------------------------------ SETTERS ------------------------------------------------ #

    def set_parameters(self, parameters):

        self.display = 1

        self.p = parameters["p"]
        self.quantities = [parameters["x0"], parameters["x1"]]
        self.beginning_angle = parameters["beginning_angle"]

    def display_nothing(self):

        self.display = 0