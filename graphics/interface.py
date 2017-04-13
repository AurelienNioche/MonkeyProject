import json
import sys
from multiprocessing import Queue, Event

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QMessageBox, QApplication

from graphics.parametrisation import ParametersContainer
from graphics.progression_bar import ProgressionBar
from graphics.trial_counter import TrialCounter
from graphics.game_window import GameWindow
from utils.utils import log
from graphics.generic import Communicant


class Interface(QWidget):

    name = "Interface"

    def __init__(self, communicant, queues, shutdown):

        QWidget.__init__(self)

        self.communicant = communicant
        self.queues = queues
        self.shutdown = shutdown
        
        self.game_window = GameWindow(queues=queues, textures_folder="textures")

        self.grid = QGridLayout()

        self.trial_counter = TrialCounter()
        self.progression_bar = ProgressionBar()
        self.parameters_container = ParametersContainer()

        self.push_button_run = QPushButton("Run!")
        # noinspection PyUnresolvedReferences
        self.push_button_run.clicked.connect(self.run)

        with open("parameters/parameters.json") as param_file:
            self.parameters = json.load(param_file)

        self.error = 0

        self.already_asked_for_saving_parameters = 0

        self.able_to_handle_message = Event()

        self.initialize()

    def initialize(self):

        self.communicant.signal.connect(self.look_for_msg)

        self.setGeometry(300, 100, 550, 480)

        self.setLayout(self.grid)

        self.grid.addWidget(self.trial_counter, 0, 0, 4, 1)
        self.grid.addWidget(self.parameters_container, 0, 0, 4, 1)
        self.grid.addWidget(self.push_button_run, 5, 0, 1, 1)
        self.grid.addWidget(self.progression_bar, 0, 0, 6, 1)

        self.progression_bar.hide()
        self.trial_counter.hide()
        self.parameters_container.show()

        self.push_button_run.setFocus()

        self.able_to_handle_message.set()

        self.show()

    def run(self):

        self.error, self.parameters = self.parameters_container.get_parameters()

        if self.error == 1:

            msg = "Bad arguments!"

            QMessageBox().warning(self, "Warning!", msg)

        else:

            self.push_button_run.setEnabled(False)

            log("Run task.", self.name)

            # Communicate parameters through the queue
            self.queues["manager"].put(("interface_run", self.parameters))

    def show_trial_counter(self):

        self.push_button_run.setText("Terminate task!")
        self.push_button_run.clicked.disconnect()
        self.push_button_run.clicked.connect(self.close_task)
        self.push_button_run.setEnabled(True)
        self.push_button_run.show()

        self.progression_bar.hide()
        self.progression_bar.shutdown()
        self.trial_counter.show()

    def show_progression_bar(self):

        self.parameters_container.hide()
        self.progression_bar.show()
        self.progression_bar.set_up()
        self.push_button_run.hide()

    def close_task(self):

        self.push_button_run.setEnabled(False)
        log("Interface: Close task.")

        self.queues["manager"].put(("interface_close_task",))

    def prepare_next_run(self):

        self.game_window.hide()

        self.push_button_run.setText("Run!")
        self.push_button_run.clicked.disconnect()
        self.push_button_run.clicked.connect(self.run)
        self.push_button_run.setEnabled(True)
        self.push_button_run.setFocus()

        self.parameters_container.show()

        self.trial_counter.hide()
        self.trial_counter.set_trial_number([0, 0])

    def closeEvent(self, event):

        if not self.already_asked_for_saving_parameters:

            with open("parameters/parameters.json") as param_file:
                old_param = json.load(param_file)

            if old_param != self.parameters:

                button_reply = \
                    QMessageBox.question(self, '', "Do you want to save the change in parameters?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if button_reply == QMessageBox.Yes:
                    with open("parameters/parameters.json", "w") as param_file:
                        json.dump(self.parameters, param_file)
                    log("Parameters saved.", self.name)
                else:
                    log("Saving of parameters aborted.", self.name)

            log("Close window", self.name)
            self.shutdown.set()
            self.queues["manager"].put(("interface_close_window",))

            self.already_asked_for_saving_parameters = 1

    def look_for_msg(self):

        message = self.queues["interface"].get()
        self.handle_message(message)

    def handle_message(self, message):

        self.able_to_handle_message.wait()
        self.able_to_handle_message.clear()

        if message[0] == "close_all_windows":
            self.game_window.standalone = True
            self.game_window.close()
            self.close()

        elif message[0] == "close_game_window":
            self.game_window.standalone = True
            self.game_window.close()

        elif message[0] == "show_progression_bar":
            self.show_progression_bar()

        elif message[0] == "track_fake_grip":
            self.game_window.track_fake_grip()

        elif message[0] == "show_game_window":
            self.game_window.show()

        elif message[0] == "show_pause_screen":
            self.game_window.show_pause_screen()

        elif message[0] == "show_stimuli":
            self.game_window.show_stimuli()

        elif message[0] == "show_results":
            self.game_window.show_results()

        elif message[0] == "show_black_screen":
            self.game_window.show_black_screen()

        elif message[0] == "show_choice":

            choice = message[1]
            self.game_window.set_choice(choice=choice)
            self.game_window.current_step = "show_choice"

        elif message[0] == "set_trial_counter":
            count = message[1]
            self.trial_counter.set_trial_number(count)

        elif message[0] == "prepare_game":
            self.prepare_game()

        elif message[0] == "prepare_next_run":
            self.prepare_next_run()

        elif message[0] == "set_gauge_quantity_and_color":

            level, color = message[1:3]
            self.game_window.set_gauge_quantity(quantity=level)
            self.game_window.set_gauge_color(color=color)
            self.game_window.frames["gauge"].repaint()

        elif message[0] == "set_gauge_quantity":

            level = message[1]
            self.game_window.set_gauge_quantity(quantity=level)
            self.game_window.frames["gauge"].repaint()

        elif message[0] == "set_gauge_color":

            color = message[1]
            self.game_window.set_gauge_color(color=color)
            self.game_window.frames["gauge"].repaint()

        elif message[0] == "show_gauge":

            self.game_window.show_gauge()

        elif message[0] == "set_stimuli_parameters":

            stimuli_parameters = message[1]
            self.game_window.set_parameters(stimuli_parameters)

        elif message[0] == "set_dice_output":

            dice_output = message[1]
            self.game_window.set_dice_output(dice_output)

        else:
            raise Exception("Interface: Message not understood: '{}'.".format(message))

        self.able_to_handle_message.set()

    def prepare_game(self):

        self.game_window.show_pause_screen()
        self.game_window.show()
        self.trial_counter.set_trial_number([0, 0])
        self.show_trial_counter()


if __name__ == "__main__":

    w = 900
    h = 0.625 * w

    app = QApplication(sys.argv)
    c = Communicant()
    q = {"graphic": Queue()}
    window = Interface(queues=q, communicant=c)
    window.show()

    sys.exit(app.exec_())
