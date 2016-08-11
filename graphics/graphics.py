from multiprocessing import Value
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QGridLayout, QHBoxLayout, QGraphicsEllipseItem, \
    QStyleOptionGraphicsItem
from PyQt5.QtGui import QPalette, QColor, QPainter, QBrush, QPen, QPixmap, QImage
from PyQt5.QtCore import QRect, QRectF, Qt, QTimer, QEvent, QObject
from collections import OrderedDict
import sys
from os.path import dirname, realpath


class Frame(QWidget):

    def __init__(self):

        QWidget.__init__(self)

        self.line_width = 0

        self.color = {"white": QColor(255, 255, 255),
                      "black": QColor(0, 0, 0),
                      "blue": QColor(114, 212, 247),
                      "green": QColor(18, 247, 41),
                      "grey": QColor(220, 220, 220)}

        self.painter = QPainter()
        self.pen = {}
        self.brush = {}

        self.create_background()
        self.prepare_pens_and_brushes()

    def create_background(self):

        pal = QPalette()
        pal.setColor(QPalette.Background, QColor(255, 255, 255))
        self.setAutoFillBackground(True)
        self.setPalette(pal)

    def prepare_pens_and_brushes(self):

        for color in self.color:

            self.pen[color] = QPen()
            self.pen[color].setColor(self.color[color])

            self.brush[color] = QBrush()
            self.brush[color].setStyle(Qt.SolidPattern)
            self.brush[color].setColor(self.color[color])

        self.pen["transparent"] = QPen()
        self.pen["transparent"].setStyle(Qt.NoPen)

        self.brush["transparent"] = QBrush()
        self.brush["transparent"].setStyle(Qt.NoBrush)

        self.brush["texture"] = QBrush()

    def paintEvent(self, e):

        self.painter.begin(self)
        self.draw()
        self.painter.end()

    def adapt_line_width(self, window_size):

        self.line_width = int(1/60. * window_size["height"])
        for c in self.color:
            self.pen[c].setWidth(self.line_width)

    def draw(self):

        pass

    def adapt_size_to_window(self, window_size):

        pass


class Pause(Frame):

    def __init__(self):
        Frame.__init__(self)

        self.rectangle_size = {"width": 0, "height": 0}
        self.margin = 0

    def draw(self):

        self.painter.setPen(self.pen["white"])
        self.painter.setBrush(self.brush["white"])
        rectangle = QRect(0,
                          0,
                          self.width(),
                          self.height())
        self.painter.drawRect(rectangle)

        self.painter.setPen(self.pen["grey"])

        rect_y = self.height() / 2. + self.margin/2. - self.rectangle_size["height"]/2.

        x_center = self.width() / 2.

        rectangle = QRect(x_center + self.margin/2.,
                          rect_y,
                          self.rectangle_size["width"],
                          self.rectangle_size["height"])

        self.painter.drawRect(rectangle)

        rectangle = QRect(x_center - self.margin / 2. - self.rectangle_size["width"],
                          rect_y,
                          self.rectangle_size["width"],
                          self.rectangle_size["height"])

        self.painter.drawRect(rectangle)

    def adapt_size_to_window(self, window_size):

        self.rectangle_size["width"] = 0.1 * window_size["width"]
        self.rectangle_size["height"] = 0.2 * window_size["width"]

        self.margin = 0.03 * window_size["width"]

        self.adapt_line_width(window_size)

        self.repaint()


class WaitingStimulus(Frame):

    def __init__(self):

        Frame.__init__(self)

        self.c_diameter = 0

    def draw(self):

        self.painter.setBrush(self.brush["black"])
        rectangle = QRect(self.width()/2.-self.c_diameter/2.,
                          self.height()/2.-self.c_diameter/2.,
                          self.c_diameter,
                          self.c_diameter)
        self.painter.drawEllipse(rectangle)

    def adapt_size_to_window(self, window_size):

        self.c_diameter = 1/30. * window_size["width"]
        self.adapt_line_width(window_size)


class Background(Frame):

    def __init__(self, color):

        Frame.__init__(self)
        self.color = color

    def draw(self):

        self.painter.setPen(self.pen[self.color])
        self.painter.setBrush(self.brush[self.color])
        rectangle = QRect(0,
                          0,
                          self.width(),
                          self.height())
        self.painter.drawRect(rectangle)

    def adapt_size_to_window(self, window_size):

        self.repaint()


class Textures(dict):

    def __init__(self):

        super(Textures, self).__init__()
        for i in range(5):
            self[i] = QImage("{}/Textures/gain{}.png".format(dirname(dirname(realpath(__file__))),
                             i))


class PieChart(Frame):

    def __init__(self, communication_mean, position, graphic_parameters):

        Frame.__init__(self)

        self.communication_mean = communication_mean

        self.position = position
        self.quantities = [0, 0]

        self.p = 0
        self.beginning_angle = 0

        self.c_diameter = 0
        self.graphic_parameters = graphic_parameters

        self.images = Textures()

        self.ellipse = None

        self.display = 0

    def adapt_size_to_window(self, window_size):

        if 'circle_size' in self.graphic_parameters:

            self.c_diameter = self.graphic_parameters["circle_size"] / 100. * window_size["height"]

        else:

            pass

        self.adapt_line_width(window_size)

        for i in self.images:

            self.images[i] = self.images[i].scaled(window_size["width"], window_size["height"],
                                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def draw(self):

        if self.display == 1:

            self.painter.setPen(self.pen["black"])

            rectangle = \
                QRectF(self.width()/2.-self.c_diameter/2.,
                       self.height()/2.-self.c_diameter/2.,
                       self.c_diameter,
                       self.c_diameter)

            ps = [self.p, 1-self.p]
            angles = [p*360*16 for p in ps]

            set_angle = self.beginning_angle*16

            for i in range(len(ps)):
                if ps[i] != 0:

                    if self.quantities[i] is not None:

                        self.brush["texture"].setTexture(QPixmap(self.images[self.quantities[i]]))
                        self.brush["texture"].setStyle(Qt.TexturePattern)
                        self.painter.setBrush(self.brush["texture"])

                        if angles[i] != 360*16:

                            self.painter.drawPie(rectangle, set_angle, angles[i])
                            set_angle += angles[i]

                        else:

                            self.painter.drawEllipse(rectangle)
                    else:
                        set_angle += angles[i]

            self.ellipse = QGraphicsEllipseItem(rectangle)
            self.ellipse.setBrush(self.brush["transparent"])
            self.ellipse.setPen(self.pen["transparent"])
            self.ellipse.paint(self.painter, QStyleOptionGraphicsItem())

        else:
            pass

    def mousePressEvent(self, event):

        if self.ellipse.contains(event.pos()):

            print("Target", self.position, "has been touched!")

            self.communication_mean.put(self.position)

    def set_parameters(self, parameters, window_size):

        self.display = 1

        self.p = parameters["p"]
        self.quantities = parameters["q"]
        self.beginning_angle = parameters["beginning_angle"]
        self.adapt_size_to_window(window_size)

        self.repaint()

    def display_nothing(self):

        self.display = 0
        self.repaint()


class StimuliContainer(QWidget):

    def __init__(self, communication_mean, graphic_parameters):

        QWidget.__init__(self)

        self.frames = OrderedDict()
        self.grid = QHBoxLayout()

        self.graphic_parameters = graphic_parameters

        self.frames["left"] = PieChart(communication_mean=communication_mean,
                                       position="left", graphic_parameters=graphic_parameters)

        self.frames["right"] = PieChart(communication_mean=communication_mean,
                                        position="right", graphic_parameters=graphic_parameters)

        self.initialize()

    def show_stimuli(self, parameters, window_size):

        for i in ["left", "right"]:

            self.frames[i].set_parameters({"p": parameters[i]["p"],
                                           "q": parameters[i]["q"],
                                           "beginning_angle": parameters[i]["beginning_angle"]}, window_size)
        self.adapt_size_to_window(window_size)
        self.show()

    def show_choice(self, stimuli_parameters, choice, window_size):

        for i in ["left", "right"]:

            if i == choice.value.decode():

                self.frames[i].set_parameters(
                    {"beginning_angle": stimuli_parameters[i]["beginning_angle"],
                     "p": stimuli_parameters[i]["p"],
                     "q": stimuli_parameters[i]["q"]},
                    window_size)

            else:
                self.frames[i].display_nothing()

        self.show()

    def show_results(self, stimuli_parameters, choice, dice_output, window_size):

        pos = choice.value.decode()

        if dice_output.value.decode() == "a":

            quantity = [stimuli_parameters[pos]["q"][0], None]

        else:
            quantity = [None, stimuli_parameters[pos]["q"][1]]

        for i in ["left", "right"]:

            if i == pos:
                self.frames[i].set_parameters(
                    {"beginning_angle": stimuli_parameters[pos]["beginning_angle"],
                     "p": stimuli_parameters[pos]["p"],
                     "q": quantity}, window_size)

            else:
                self.frames[i].display_nothing()

        self.show()

    def initialize(self):

        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        for i in self.frames.values():
            self.grid.addWidget(i)
            i.show()

        self.setLayout(self.grid)

    def adapt_size_to_window(self, window_size):

        for i in self.frames.values():
            i.adapt_size_to_window(window_size)


class Window(QMainWindow):

    def __init__(self):

        super(Window, self).__init__()

        self.setGeometry(300, 300, 480, 300)

        self.central_area = QWidget()
        self.setCentralWidget(self.central_area)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.central_area.setLayout(self.grid)

        self.frames = OrderedDict()

    def initialize(self):

        for i in self.frames.values():
            i.adapt_size_to_window({"width": self.width(), "height": self.height()})
            self.grid.addWidget(i, 0, 0)
            i.hide()

        self.show()

    def update_size(self):

        for i in self.frames.values():
            i.adapt_size_to_window({"width": self.width(), "height": self.height()})
        self.hide()
        self.show()

    def changeEvent(self, event):

        if event.type() == QEvent.WindowStateChange:

            QTimer().singleShot(0, self.update_size)

    def resizeEvent(self, event):

        QTimer().singleShot(0, self.update_size)


class GameWindow(Window):

    def __init__(self, keyboard_queues, keys, shutdown_event,
                 current_frame, stimuli_parameters, choice_queue,
                 choice,
                 dice_output,
                 display, graphic_parameters):

        super(GameWindow, self).__init__()

        self.setWindowTitle('Touch the circle!')

        self.shutdown_event = shutdown_event

        self.display = display

        self.keys = keys
        self.keyboard_queues = keyboard_queues

        self.stimuli_parameters = stimuli_parameters
        self.graphic_parameters = graphic_parameters
        self.choice = choice
        self.dice_output = dice_output

        self.current_frame = current_frame
        self.previous_frame = None

        self.frames["stimuli"] = StimuliContainer(communication_mean=choice_queue,
                                                  graphic_parameters=graphic_parameters)
        self.frames["punishment"] = Background(color="black")
        self.frames["inter_trial"] = Background(color="white")
        self.frames["fixation_dot"] = WaitingStimulus()
        self.frames["pause"] = Pause()

        self.cursor_visible = 1

        self.timer = QTimer()
        self.timer.setInterval(50)
        # noinspection PyUnresolvedReferences
        self.timer.timeout.connect(self.update_frame)

        self.initialize()

        self.timer.start()

    def update_frame(self):

        current_frame = self.current_frame.value.decode()

        if self.previous_frame == current_frame:

            pass

        else:

            self.previous_frame = current_frame

            for i in self.frames.values():
                i.hide()

            w_size = {"width": self.width(), "height": self.height()}

            if current_frame == "stimuli":

                self.frames["stimuli"].show_stimuli(
                    self.stimuli_parameters, w_size)

            elif current_frame == "choice":

                self.frames["stimuli"].show_choice(
                    stimuli_parameters=self.stimuli_parameters,
                    choice=self.choice,
                    window_size=w_size)

            elif current_frame == "result":

                self.frames["stimuli"].show_results(
                    stimuli_parameters=self.stimuli_parameters,
                    choice=self.choice,
                    dice_output=self.dice_output,
                    window_size=w_size)

            else:
                self.frames[current_frame].show()

    def keyPressEvent(self, event):

        if not event.isAutoRepeat():

            for q in self.keyboard_queues:
                q.put([1, event.key()])
            self.keys.append(event.key())

            if event.key() == Qt.Key_F and self.keys.count(16777249) == 1 \
                    and not self.isFullScreen():

                self.showFullScreen()

                self.update_size()

            elif event.key() == Qt.Key_Escape:

                if self.isFullScreen():
                    self.showNormal()
                else:
                    pass

            elif event.key() == Qt.Key_X and self.keys.count(16777249) == 1:

                if self.cursor_visible == 0:
                    self.unsetCursor()
                    self.cursor_visible = 1
                else:
                    self.setCursor(Qt.BlankCursor)
                    self.cursor_visible = 0

            event.accept()

    def keyReleaseEvent(self, event):

        for q in self.keyboard_queues:
            q.put([0, event.key()])
        self.keys.remove(event.key())
        event.accept()

    def closeEvent(self, event):

        if self.isVisible():

            print("GameWindow: DEAD.")

            if not self.shutdown_event.is_set():

                self.shutdown_event.set()

            for q in self.keyboard_queues:
                q.put(None)

            self.display.value = 0

            if self.isFullScreen():

                self.showNormal()
                QTimer().singleShot(1, self.close)
                QTimer().singleShot(2, self.destroy)


class WindowManager(QObject):

    def __init__(self, display, keyboard_queues, keys, choice, choice_queue, shutdown_event,
                 general_shutdown_event,
                 current_frame, stimuli_parameters, dice_output, sound_instructions,
                 confirmation_opening_window, graphic_parameters):

        super(WindowManager, self).__init__()

        self.display = display
        self.shutdown_event = shutdown_event
        self.general_shutdown_event = general_shutdown_event

        self.stimuli_parameters = stimuli_parameters
        self.graphic_parameters = graphic_parameters
        self.dice_output = dice_output

        self.choice = choice
        self.choice_queue = choice_queue

        self.current_frame = current_frame
        self.sound_instructions = sound_instructions

        self.keyboard_queues = keyboard_queues
        self.keys = keys

        self.confirmation_opening_window = confirmation_opening_window

        self.timer = QTimer()
        # noinspection PyUnresolvedReferences
        self.timer.timeout.connect(self.check_for_window_command)
        self.timer.setInterval(500)
        self.timer.start()

        self.window = None

        self.exist_window = Value('i')
        self.exist_window.value = 0

    def check_for_window_command(self):

        show = self.display.value

        if show == 1:

            if not self.exist_window.value:

                print("WindowManager: Open window.")

                self.window = GameWindow(
                    keyboard_queues=self.keyboard_queues,
                    keys=self.keys,
                    choice=self.choice,
                    choice_queue=self.choice_queue,
                    shutdown_event=self.shutdown_event,
                    current_frame=self.current_frame,
                    stimuli_parameters=self.stimuli_parameters,
                    graphic_parameters=self.graphic_parameters,
                    dice_output=self.dice_output,
                    display=self.display)

                self.window.show()

                self.exist_window.value = 1
                self.confirmation_opening_window.put(1)

        elif show == 0:

            if self.exist_window.value == 1:

                print("WindowManager: Close window.")
                self.window.close()

                self.exist_window.value = 0

        if self.general_shutdown_event.is_set():

            if self.exist_window.value == 1:
                self.window.close()

            self.timer.stop()
            self.sound_instructions.put(None)

            print("WindowManager: DEAD.")


if __name__ == "__main__":

    app = QApplication(sys.argv)

    sys.exit(app.exec_())
