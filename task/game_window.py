from PyQt5.QtWidgets import QWidget, QApplication, QGraphicsEllipseItem, \
    QStyleOptionGraphicsItem, QGridLayout, QMainWindow
from PyQt5.QtGui import QPalette, QColor, QPainter, QBrush, QPen, QPixmap, QImage
from PyQt5.QtCore import QRectF, Qt, QPoint, QTimer
from collections import OrderedDict
from multiprocessing import Queue
import sys
import numpy as np


# ----------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------ FRAME ---------------------------------------------------- #
# ----------------------------------------------------------------------------------------------------------- #


class Colors:
    white = QColor(255, 255, 255)
    black = QColor(0, 0, 0)
    blue = QColor(114, 212, 247)
    grey = QColor(220, 220, 220)
    green = QColor(18, 247, 41)
    red = QColor(255, 0, 0)

# ----------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------ GAUGE ---------------------------------------------------- #
# ----------------------------------------------------------------------------------------------------------- #


class Pause(QWidget):

    def __init__(self):
        super().__init__()

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

        pen.setColor(QColor(255, 255, 255))
        painter.setPen(pen)
        brush.setColor((QColor(255, 255, 255)))
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

# ----------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------ GAUGE ---------------------------------------------------- #
# ----------------------------------------------------------------------------------------------------------- #


class Gauge(QWidget):

    def __init__(self, color="black"):

        super().__init__()

        self.color = color
        self.token_number = 0

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

        pen.setColor(QColor(0, 0, 0))  # Black
        pen.setWidth(line_width)
        painter.setPen(pen)

        # brush.setColor()
        #
        # self.painter.setBrush(self.brush["transparent"])
        # self.painter.setPen(self.pen[self.color])

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

        self.painter.drawLine(
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
        painter.setPen()

        brush.setColor(getattr(Colors, self.color))
        painter.setBrush()

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
        self.repaint()

    def set_color(self, color):

        self.color = color
        self.repaint()
# ----------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------ PIE CHART ------------------------------------------------ #
# ----------------------------------------------------------------------------------------------------------- #


class PieChart(QWidget):

    textures_folder = "textures"

    def __init__(self, position):

        super().__init__()

        self.quantity_possibilities = np.arange(-4, 5, 1)

        self.position = position
        self.quantities = [0, 0]

        self.p = 0
        self.beginning_angle = 0

        self.ellipse = None

        self.display = 1

        self.textures = {}

        self.load_textures()

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

        self.repaint()

    def display_nothing(self):

        self.display = 0
        self.repaint()

# ----------------------------------------------------------------------------------------------------------- #
# ------------------------------------------ GAME WINDOW ---------------------------------------------------- #
# ----------------------------------------------------------------------------------------------------------- #


class GameWindow(QMainWindow):

    def __init__(self, queue, standalone=False):

        QWidget.__init__(self)

        self.queue = queue

        self.fake_grip_value = None
        self.fake_grip_queue = None

        self.main_widget = QWidget()
        self.frames = OrderedDict()
        self.grid = QGridLayout()

        self.current_step = "show_pause_screen"
        self.previous_step = None

        self.control_modifier = False
        self.cursor_visible = True

        self.standalone = standalone

        self.parameters = {
            "left_p": 0.25,
            "left_x0": 3,
            "left_x1": 0,
            "left_beginning_angle": 5,
            "right_p": 0.5,
            "right_x0": 1,
            "right_x1": 0,
            "right_beginning_angle": 140
        }

        self.choice = "left"

        self.dice_output = 0

        self.timer = QTimer()

        self.initialize()

# ------------------------------------------------------ INITIALIZE ------------------------------------------------ #

    def initialize(self):

        width = 900
        height = 0.625 * width

        self.setCentralWidget(self.main_widget)

        self.setGeometry(100, 100, width, height)

        self.frames["left"] = PieChart(position="left")
        self.frames["gauge"] = Gauge()
        self.frames["right"] = PieChart(position="right")
        self.frames["black_screen"] = Frame(background_color="black")
        self.frames["pause"] = Pause()

        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)

        self.grid.addWidget(self.frames["left"], 0, 0, 1, 3)
        self.grid.addWidget(self.frames["gauge"], 0, 3, 1, 1)
        self.grid.addWidget(self.frames["right"], 0, 4, 1, 3)
        self.grid.addWidget(self.frames["black_screen"], 0, 0, 1, 7)
        self.grid.addWidget(self.frames["pause"], 0, 0, 1, 7)

        self.main_widget.setLayout(self.grid)

        self.hide_black_screen()
        self.hide_pause_screen()
        self.hide_stimuli()

        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_display)
        self.timer.start()

# --------------------------------------------------------- DISPLAY ------------------------------------------------ #

    def update_display(self):

        if self.current_step == "hide":
            if self.isFullScreen():
                self.showMinimized()
            elif self.isVisible():

                self.hide()

        elif self.current_step != self.previous_step:

            print("GameWindow: ", self.current_step)
            if self.current_step == "show_stimuli":

                self.hide_black_screen()
                self.hide_pause_screen()
                self.show_stimuli()

            elif self.current_step == "show_black_screen":

                self.hide_pause_screen()
                self.hide_stimuli()
                self.show_black_screen()

            elif self.current_step == "show_pause_screen":

                self.show_pause_screen()
                self.hide_black_screen()
                self.hide_stimuli()

            elif self.current_step == "show_choice":

                self.hide_black_screen()
                self.hide_pause_screen()
                self.show_choice()

            elif self.current_step == "show_results":

                self.hide_black_screen()
                self.hide_pause_screen()
                self.show_results()

            elif self.current_step == "show_gauge":

                self.hide_pause_screen()
                self.hide_black_screen()
                self.hide_stimuli()
                self.show_gauge()

            elif self.current_step == "hide":
                pass

            else:

                print("ERROR: WRONG COMMAND FOR GAME WINDOW: ", self.current_step)

            self.previous_step = self.current_step

    def show_stimuli(self):

        for i in ["left", "right"]:

            self.frames[i].set_parameters(
                {
                    "beginning_angle": self.parameters["{}_beginning_angle".format(i)],
                    "p": self.parameters["{}_p".format(i)],
                    "x0": self.parameters["{}_x0".format(i)],
                    "x1": self.parameters["{}_x1".format(i)]
                 })

    def hide_stimuli(self):

        for i in ["left", "right"]:

            self.frames[i].display_nothing()

    def show_choice(self):

        for i in ["left", "right"]:

            if i == self.choice:

                self.frames[i].set_parameters(
                    {
                        "beginning_angle": self.parameters["{}_beginning_angle".format(i)],
                        "p": self.parameters["{}_p".format(i)],
                        "x0": self.parameters["{}_x0".format(i)],
                        "x1": self.parameters["{}_x1".format(i)]
                     })

            else:
                self.frames[i].display_nothing()

    def show_results(self):

        if self.dice_output == 0:

            x0 = self.parameters["{}_x0".format(self.choice)]
            x1 = None

        else:
            x0 = None
            x1 = self.parameters["{}_x1".format(self.choice)]

        for i in ["left", "right"]:

            if i == self.choice:
                self.frames[i].set_parameters(
                    {
                        "beginning_angle": self.parameters["{}_beginning_angle".format(self.choice)],
                        "p": self.parameters["{}_p".format(self.choice)],
                        "x0": x0,
                        "x1": x1
                    })

            else:
                self.frames[i].display_nothing()

    def show_gauge(self):

        self.frames["gauge"].show()

    def show_black_screen(self):

        self.frames["black_screen"].show()

    def hide_black_screen(self):

        self.frames["black_screen"].hide()

    def show_pause_screen(self):

        self.frames["pause"].show()

    def hide_pause_screen(self):

        self.frames["pause"].hide()

# ------------------------------------------------ SETTERS --------------------------------------------------------- #

    def set_choice(self, choice):

        self.choice = choice

    def set_parameters(self, parameters):

        self.parameters = parameters

    def set_dice_output(self, dice_output):

        self.dice_output = dice_output

    def set_gauge_color(self, color):

        self.frames["gauge"].set_color(color=color)

    def set_gauge_quantity(self, **kwargs):

        self.frames["gauge"].set_quantity(quantity=kwargs["quantity"])

# ------------------------------------------------ FAKE GRIP ------------------------------------------------------- #

    def track_fake_grip(self, queue, value):

        self.fake_grip_queue = queue
        self.fake_grip_value = value

    def stop_track_fake_grip(self):

        self.fake_grip_queue = None
        self.fake_grip_value = None

# ------------------------------------------------ MOUSE ----------------------------------------------------------- #

    def mousePressEvent(self, event):

        print("GameWindow: MOUSE CLICK.")
        if self.current_step == "show_stimuli":

            if self.frames["left"].ellipse.contains(event.pos()):
                print("GameWindow: CLICK LEFT.")
                self.queue.put(("game_left", ))

            if self.frames["right"].ellipse.contains(QPoint(event.x() - self.width()*(4/7), event.y())):
                print("GameWindow: CLICK RIGHT.")
                self.queue.put(("game_right", ))

            else:
                pass

# ------------------------------------------------ KEYBOARD -------------------------------------------------------- #

    def keyPressEvent(self, event):

        # print("GameWindow: KEY PRESSED.")

        if event.key() == Qt.Key_Control:

            self.control_modifier = True

        elif event.key() == Qt.Key_Escape:

            if self.isFullScreen():
                self.showNormal()

        elif self.current_step == "show_pause_screen" and event.key() == Qt.Key_Space:

            if not event.isAutoRepeat():
                print("GameWindow: PRESS 'PLAY'.")
                self.queue.put(("game_play", ))

        elif self.control_modifier and event.key() == Qt.Key_X:

            if self.cursor_visible:
                self.setCursor(Qt.BlankCursor)
                self.cursor_visible = False

            else:
                self.unsetCursor()
                self.cursor_visible = True

        elif self.fake_grip_queue and event.key() == Qt.Key_P:

            if not event.isAutoRepeat():

                self.fake_grip_queue.put(1)
                self.fake_grip_value.value = 1

    def keyReleaseEvent(self, event):

        if event.key() == Qt.Key_Control:

            self.control_modifier = False

        elif self.fake_grip_queue and event.key() == Qt.Key_P:

            self.fake_grip_queue.put(0)
            self.fake_grip_value.value = 0

# ------------------------------------------------ CLOSE ------------------------------------------------ #

    def closeEvent(self, event):

        print("GameWindow: Close window.")
        self.queue.put(("game_close_window", ))
        if self.standalone:
            event.accept()
        else:
            event.ignore()

# ------------------------------------------------ MAIN ------------------------------------------------ #

if __name__ == "__main__":

    q = Queue()

    app = QApplication(sys.argv)

    PieChart.textures_folder = "../textures"

    window = GameWindow(queue=q, standalone=True)
    window.show_stimuli()
    # window.show_choice(parameters=st_parameters, choice=ch)
    # window.show_results(parameters=st_parameters, choice=ch, dice_output=d)
    window.show_gauge()
    # window.hide_stimuli()
    # window.show_black_screen()
    # window.hide_black_screen()
    # window.show_pause_screen()

    window.show()

    sys.exit(app.exec_())