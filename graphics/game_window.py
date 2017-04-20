from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from collections import OrderedDict
from multiprocessing import Queue, Event
import sys

from utils.utils import log
from graphics.generic import Frame
from graphics.gauge import Gauge
from graphics.pie_chart import PieChart
from graphics.pause import Pause


class GameWindow(QMainWindow):

    name = "GameWindow"
    
    init_x = 100
    init_y = 100
    init_width = 900
    init_height = 0.625 * init_width

    def __init__(self, queues, textures_folder, standalone=False):

        QWidget.__init__(self)

        self.queues = queues
        self.standalone = standalone
        self.textures_folder = textures_folder

        self.fake_grip_value = None
        self.fake_grip_queue = None

        self.main_widget = QWidget()
        self.frames = OrderedDict()
        self.grid = QGridLayout()

        self.control_modifier = False
        self.cursor_visible = True

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

        self.detect_choices = Event()
        self.detect_pause_break = Event()

        self.initialize()

# ------------------------------------------------------ INITIALIZE ------------------------------------------------ #

    def initialize(self):

        self.setCentralWidget(self.main_widget)

        self.setGeometry(self.init_x, self.init_y, self.init_width, self.init_height)

        self.frames["left"] = PieChart(position="left", textures_folder=self.textures_folder)
        self.frames["gauge"] = Gauge()
        self.frames["right"] = PieChart(position="right", textures_folder=self.textures_folder)
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

        self.frames["black_screen"].hide()
        self.hide_pause_screen()
        self.hide_stimuli()

# --------------------------------------------------------- DISPLAY ------------------------------------------------ #

    def hide(self):

        if self.isFullScreen():

            self.showMinimized()
            QTimer.singleShot(100, self.hide)

        elif self.isVisible():

            super().hide()

    def show_stimuli(self):

        self.detect_choices.set()

        for i in ["left", "right"]:

            self.frames[i].set_parameters(
                {
                    "beginning_angle": self.parameters["{}_beginning_angle".format(i)],
                    "p": self.parameters["{}_p".format(i)],
                    "x0": self.parameters["{}_x0".format(i)],
                    "x1": self.parameters["{}_x1".format(i)]
                 })

            self.frames[i].repaint()

    def hide_stimuli(self):

        self.detect_choices.clear()

        for i in ["left", "right"]:

            self.frames[i].display_nothing()
            self.frames[i].repaint()

    def show_choice(self):

        self.frames["black_screen"].hide()
        self.hide_pause_screen()

        for i in ["left", "right"]:

            if i == self.choice:

                self.frames[i].set_parameters(
                    {
                        "beginning_angle": self.parameters["{}_beginning_angle".format(i)],
                        "p": self.parameters["{}_p".format(i)],
                        "x0": self.parameters["{}_x0".format(i)],
                        "x1": self.parameters["{}_x1".format(i)]
                     })
                self.frames[i].repaint()

            else:
                self.frames[i].display_nothing()
                self.frames[i].repaint()

    def show_results(self):

        self.frames["black_screen"].hide()
        self.hide_pause_screen()

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

                self.frames[i].repaint()

            else:
                self.frames[i].display_nothing()

                self.frames[i].repaint()
        self.frames["gauge"].repaint()

    def show_gauge(self):

        self.hide_pause_screen()
        self.frames["black_screen"].hide()
        self.hide_stimuli()

        self.frames["gauge"].show()

    def show_black_screen(self):

        self.hide_pause_screen()
        self.hide_stimuli()
        self.frames["black_screen"].show()

    def show_pause_screen(self):

        self.detect_pause_break.set()
        self.frames["black_screen"].hide()
        self.hide_stimuli()
        self.frames["pause"].show()

    def hide_pause_screen(self):

        self.detect_pause_break.clear()
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

    def track_fake_grip(self):

        self.fake_grip_queue = self.queues["grip_queue"]
        self.fake_grip_value = self.queues["grip_value"]

    def stop_track_fake_grip(self):

        self.fake_grip_queue = None
        self.fake_grip_value = None

# ------------------------------------------------ MOUSE ----------------------------------------------------------- #

    def mousePressEvent(self, event):

        log("MOUSE CLICK.", self.name)
        if self.detect_choices.is_set():

            if self.frames["left"].ellipse.contains(event.pos()):
                log("CLICK LEFT.", self.name)
                self.queues["manager"].put(("game", "left", ))

            if self.frames["right"].ellipse.contains(QPoint(event.x() - self.width()*(4/7), event.y())):
                log("CLICK RIGHT.", self.name)
                self.queues["manager"].put(("game", "right", ))

            else:
                pass

# ------------------------------------------------ KEYBOARD -------------------------------------------------------- #

    def keyPressEvent(self, event):

        # log("GameWindow: KEY PRESSED.")

        if event.key() == Qt.Key_Control:

            self.control_modifier = True

        elif event.key() == Qt.Key_Escape:

            if self.isFullScreen():
                self.showNormal()

        elif self.detect_pause_break.is_set() and event.key() == Qt.Key_Space:

            if not event.isAutoRepeat():
                log("PRESS 'PLAY'.", self.name)
                self.queues["manager"].put(("game", "play", ))

        elif self.control_modifier and event.key() == Qt.Key_X:

            if self.cursor_visible:
                self.setCursor(Qt.BlankCursor)
                self.cursor_visible = False

            else:
                self.unsetCursor()
                self.cursor_visible = True

        elif self.fake_grip_queue and event.key() == Qt.Key_P:

            if not event.isAutoRepeat():
                log("PRESS 'P'.", self.name)

                self.fake_grip_queue.put(1)
                self.fake_grip_value.value = 1

        elif self.control_modifier and event.key() == Qt.Key_F:

            self.showFullScreen()

    def keyReleaseEvent(self, event):

        if event.key() == Qt.Key_Control:

            self.control_modifier = False

        elif self.fake_grip_queue and event.key() == Qt.Key_P:

            self.fake_grip_queue.put(0)
            self.fake_grip_value.value = 0

# ----------------------------------------- RESIZE EVENT ------------------------------------------------ #

    def resizeEvent(self, event):

        if not self.cursor_visible:

            self.unsetCursor()
            self.cursor_visible = True

# ------------------------------------------------ CLOSE ------------------------------------------------ #

    def closeEvent(self, event):

        log("Received demand for closing window.", self.name)
        self.queues["manager"].put(("game", "close", ))
        if self.standalone:
            log("Demand accepted for closing window.", self.name)
            event.accept()
        else:
            log("Demand ignored for closing window.", self.name)
            event.ignore()

# ------------------------------------------------ MAIN ------------------------------------------------ #


def main():

    q = {"manager": Queue(), "interface": Queue()}

    app = QApplication(sys.argv)

    textures_folder = "../textures"

    window = GameWindow(queues=q, textures_folder=textures_folder, standalone=True)
    window.show_stimuli()
    # window.show_choice(parameters=st_parameters, choice=ch)
    # window.show_results(parameters=st_parameters, choice=ch, dice_output=d)
    # window.show_gauge()
    # window.hide_stimuli()
    # window.show_black_screen()
    # window.hide_black_screen()
    # window.show_pause_screen()

    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":

    main()