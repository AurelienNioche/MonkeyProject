from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QLabel, QMessageBox, QApplication, QSpacerItem, \
    QProgressBar
from multiprocessing import Queue
import sys
import json

from task.parametrisation import ParametersContainer
from utils.utils import log


class TrialCounter(QWidget):

    def __init__(self):

        QWidget.__init__(self)

        self.grid = QGridLayout()

        self.trial_label = QLabel("000")
        self.trial_c_label = QLabel("Trials")
        self.trial_without_errors_label = QLabel("000")
        self.trial_c_without_errors_label = QLabel("Trials without errors")

        self.initialize()

    def initialize(self):

        font = QFont()
        font.setPointSize(64)

        self.trial_label.setFont(font)
        self.trial_label.setContentsMargins(30, 30, 30, 0)

        self.trial_c_label.setContentsMargins(30, 0, 30, 30)

        self.trial_without_errors_label.setFont(font)
        self.trial_without_errors_label.setContentsMargins(30, 30, 30, 0)

        self.trial_c_without_errors_label.setContentsMargins(30, 0, 30, 30)

        self.setLayout(self.grid)
        spacer_row_span = 4
        self.grid.addItem(QSpacerItem(1, 1), 0, 1, spacer_row_span, 1)
        self.grid.addWidget(self.trial_label, spacer_row_span + 1, 0, Qt.AlignCenter)
        self.grid.addWidget(self.trial_c_label, spacer_row_span + 2, 0, Qt.AlignCenter)
        self.grid.addWidget(self.trial_without_errors_label, spacer_row_span + 1, 1, Qt.AlignCenter)
        self.grid.addWidget(self.trial_c_without_errors_label, spacer_row_span + 2, 1, Qt.AlignCenter)
        self.grid.addItem(QSpacerItem(1, 1), spacer_row_span + 3, 1, spacer_row_span, 1)

        # self.update_trial_number([0, 0])

    def set_trial_number(self, trial_n):

        self.trial_label.setText(str(trial_n[0]).zfill(3))
        self.trial_without_errors_label.setText(str(trial_n[1]).zfill(3))


class ProgressionBar(QWidget):

    def __init__(self):

        QWidget.__init__(self)

        self.grid = QGridLayout()

        self.label = QLabel("Setting up a few things...")
        self.progression_bar = QProgressBar()

        self.initialize()

    def initialize(self):

        font = QFont()
        font.setPointSize(14)

        self.label.setFont(font)
        self.label.setContentsMargins(30, 30, 30, 0)

        self.setLayout(self.grid)
        spacer_row_span = 10
        self.grid.addItem(QSpacerItem(0, 1), 0, 0, spacer_row_span, 10)
        self.grid.addWidget(self.label, spacer_row_span + 1, 5, Qt.AlignCenter)
        self.grid.addItem(QSpacerItem(0, 0), spacer_row_span + 2, 1, 2, 10)
        self.grid.addWidget(self.progression_bar, spacer_row_span + 3 + 2, 3, 1, 5)
        self.grid.addItem(QSpacerItem(0, 0), spacer_row_span + 5, 1, spacer_row_span, 10)

    def set_up(self):
        self.progression_bar.reset()
        self.progression_bar.setMaximum(0)
        self.progression_bar.setMinimum(0)
        self.progression_bar.setValue(0)

    def shutdown(self):

        self.progression_bar.setMaximum(100)
        self.progression_bar.setValue(100)


class Interface(QWidget):

    def __init__(self, queue):

        QWidget.__init__(self)

        self.queue = queue

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

        self.initialize()

    def initialize(self):

        self.setGeometry(300, 300, 550, 480)

        self.setLayout(self.grid)

        self.grid.addWidget(self.trial_counter, 0, 0, 4, 1)
        self.grid.addWidget(self.parameters_container, 0, 0, 4, 1)
        self.grid.addWidget(self.push_button_run, 5, 0, 1, 1)
        self.grid.addWidget(self.progression_bar, 0, 0, 6, 1)

        self.progression_bar.hide()
        self.trial_counter.hide()
        self.parameters_container.show()

        self.push_button_run.setFocus()

    def run(self):

        self.error, self.parameters = self.parameters_container.get_parameters()

        if self.error == 1:

            msg = "Bad arguments!"

            QMessageBox().warning(self, "Warning!", msg)

        else:

            self.push_button_run.setEnabled(False)

            log("Interface: Run task.")

            # Communicate parameters through the queue
            self.queue.put(("interface_run", self.parameters))

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

        self.queue.put(("interface_close_task",))

    def prepare_next_run(self):

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
                    log('Interface: parameters saved.')
                else:
                    log('Interface: saving of parameters aborted.')

            log("Interface: Close window")
            self.queue.put(("interface_close_window",))

            self.already_asked_for_saving_parameters = 1


if __name__ == "__main__":

    w = 900
    h = 0.625 * w

    app = QApplication(sys.argv)
    q = Queue()
    window = Interface(queue=q)
    window.show()

    sys.exit(app.exec_())
