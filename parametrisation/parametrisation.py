# coding=utf-8
from PyQt5.QtCore import QTimer, QThread, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QLabel, QLineEdit, \
    QRadioButton, QCheckBox, QMessageBox
from collections import OrderedDict
import queue


class MyThread(QThread):

    def __init__(self, target):

        super(QThread, self).__init__()

        self.target = target

    def run(self):

        self.target()


class ParametersContainer(QWidget):

    def __init__(self):

        QWidget.__init__(self)

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.parameters = OrderedDict()

        self.parameters["circle_size"] = \
            Parameter(text="Circle size (% window height)", initial_value=50,
                      value_range=[1, 100])

        self.parameters["valve_opening_time"] = \
            Parameter(text="Valve opening time (ms)", initial_value=100,
                      value_range=[1, 10000])

        self.parameters["grasping_time"] = \
            Parameter(text="Grasping time (ms)",
                      initial_value=250,
                      value_range=[1, 100000])

        self.parameters["fixation_dot_time"] = \
            MinMaxParameter(text="Fixation dot time (ms)", initial_value_min=500,
                            initial_value_max=750,
                            value_range_min=[1, 100000],
                            value_range_max=[1, 100000])

        self.parameters["max_decision_time"] = \
            Parameter(text="Max decision time (ms)", initial_value=5000,
                      value_range=[1, 100000])

        self.parameters["max_return_time"] = \
            Parameter(text="Max return time (ms)", initial_value=5000,
                      value_range=[1, 100000])

        self.parameters["result_display_time"] = \
            Parameter(text="Result display time (ms)", initial_value=950,
                      value_range=[1, 100000])

        self.parameters["inter_trial_time"] = \
            MinMaxParameter(text="Inter-trial time (ms)", initial_value_min=500,
                            initial_value_max=750,
                            value_range_min=[1, 100000],
                            value_range_max=[1, 100000])

        self.parameters["punishment_time"] = \
            Parameter(text="Punishment time (ms)", initial_value=2000,
                      value_range=[1, 100000])

        self.parameters["monkey"] = \
            RadioParameter(text="Monkey", text_radio1="Havane", text_radio2="Gladys")

        self.parameters["save"] = \
            CheckParameter(text="Save results")

        for i, p in enumerate(self.parameters.keys()):

            self.parameters[p].add_to_grid(grid=self.grid, line=i)


class Parameter(object):

    def __init__(self, text, initial_value, value_range):

        self.initial_value = initial_value
        self.value_range = value_range

        self.label = QLabel(text)
        self.edit = QLineEdit(str(initial_value))

    def get_value(self):

        try:
            value = float(self.edit.text())

            if self.value_range[0] <= value <= self.value_range[1]:
                return value
            else:
                return "error"

        except ValueError:

            return "error"

    def add_to_grid(self, grid, line):

        grid.addWidget(self.label, line, 0)
        grid.addWidget(self.edit, line, 1)


class ListParameter(object):

    def __init__(self, text, initial_value, value_range):

        self.initial_value = initial_value
        self.value_range = value_range

        self.label = QLabel(text)
        self.edit = QLineEdit(str(initial_value))

    def get_value(self):

        e = 0

        try:
            value = [float(i) for i in self.edit.text().split(",")]

            for i in value:

                if self.value_range[0] <= i <= self.value_range[1]:
                    pass
                else:
                    e += 1

            if e == 0:
                return value
            else:
                return "error"

        except ValueError:

            return "error"

    def add_to_grid(self, grid, line):

        grid.addWidget(self.label, line, 0)
        grid.addWidget(self.edit, line, 1)


class MinMaxParameter(object):

    def __init__(self, text, initial_value_min, initial_value_max, value_range_min, value_range_max):

        self.initial_value_min = initial_value_min
        self.initial_value_max = initial_value_max
        self.value_range_min = value_range_min
        self.value_range_max = value_range_max

        self.label = QLabel(text)
        self.edit_min = QLineEdit(str(initial_value_min))
        self.label_inter = QLabel("to")
        self.edit_max = QLineEdit(str(initial_value_max))

    def get_value(self):

        try:
            value_min = float(self.edit_min.text())
            value_max = float(self.edit_max.text())

            if self.value_range_min[0] <= value_min <= self.value_range_min[1] \
                    and self.value_range_max[0] <= value_max <= self.value_range_max[1]:
                return [value_min, value_max]
            else:
                return "error"

        except ValueError:

            return "error"

    def add_to_grid(self, grid, line):

        grid.addWidget(self.label, line, 0)
        grid.addWidget(self.edit_min, line, 1)
        grid.addWidget(self.label_inter, line, 2)
        grid.addWidget(self.edit_max, line, 3)


class RadioParameter(object):

    def __init__(self, text, text_radio1, text_radio2):

        self.label = QLabel(text)

        self.radio1 = QRadioButton(text_radio1)
        self.radio2 = QRadioButton(text_radio2)

        self.radio2.setChecked(True)

    def get_value(self):

        if self.radio1.isChecked():

            return self.radio1.text()

        elif self.radio2.isChecked():

            return self.radio2.text()

        else:

            return "error"

    def add_to_grid(self, grid, line):

        grid.addWidget(self.label, line, 0)
        grid.addWidget(self.radio1, line, 1)
        grid.addWidget(self.radio2, line, 3)


class CheckParameter(object):

    def __init__(self, text):

        self.label = QLabel(text)
        self.check_box = QCheckBox()

        self.check_box.setChecked(1)

    def get_value(self):

        return self.check_box.isChecked()

    def add_to_grid(self, grid, line):

        grid.addWidget(self.label, line, 0)
        grid.addWidget(self.check_box, line, 1)


class TrialCounter(QWidget):

    def __init__(self, trial_queue):

        QWidget.__init__(self)

        self.trial_queue = trial_queue

        self.grid = QGridLayout()

        self.trial_label = QLabel("000")
        self.trial_c_label = QLabel("Trials")
        self.trial_without_errors_label = QLabel("000")
        self.trial_c_without_errors_label = QLabel("Trials without errors")

        self.timer = QTimer()
        self.timer.setInterval(50)
        # noinspection PyUnresolvedReferences
        self.timer.timeout.connect(self.update_trial_number)

        self.add_to_grid()

    def update_trial_number(self):

        try:

            trial_n = self.trial_queue.get(timeout=0.05)

            self.trial_label.setText(str(trial_n[0]).zfill(3))
            self.trial_without_errors_label.setText(str(trial_n[1]).zfill(3))

        except queue.Empty:
            pass

    def start(self):
        self.timer.start()

    def stop(self):

        self.timer.stop()

    def add_to_grid(self):

        font = QFont()
        font.setPointSize(64)

        self.trial_label.setFont(font)
        self.trial_label.setContentsMargins(30, 30, 30, 0)

        self.trial_c_label.setContentsMargins(30, 0, 30, 30)

        self.trial_without_errors_label.setFont(font)
        self.trial_without_errors_label.setContentsMargins(30, 30, 30, 0)

        self.trial_c_without_errors_label.setContentsMargins(30, 0, 30, 30)

        self.setLayout(self.grid)
        self.grid.addWidget(self.trial_label, 0, 0, Qt.AlignCenter)
        self.grid.addWidget(self.trial_c_label, 1, 0, Qt.AlignCenter)
        self.grid.addWidget(self.trial_without_errors_label, 0, 1, Qt.AlignCenter)
        self.grid.addWidget(self.trial_c_without_errors_label, 1, 1, Qt.AlignCenter)


class Interface(QWidget):

    def __init__(self, parameters_values, shutdown_event, general_shutdown, trial_queue):

        QWidget.__init__(self)

        self.trial_queue = trial_queue
        self.shutdown_event = shutdown_event
        self.general_shutdown_event = general_shutdown

        self.parameters_values = parameters_values

        self.grid = QGridLayout()

        self.parameters_container = ParametersContainer()

        self.push_button1 = QPushButton("Run!")
        # noinspection PyUnresolvedReferences
        self.push_button1.clicked.connect(self.run)

        self.trial_counter = TrialCounter(trial_queue=self.trial_queue)

        self.timer = QTimer()
        self.timer.setInterval(50)
        # noinspection PyUnresolvedReferences
        self.timer.timeout.connect(self.check_task_running)

        self.initialize()

    def initialize(self):

        self.setGeometry(300, 300, 550, 480)
        self.setWindowTitle('Set parameters')

        self.setLayout(self.grid)

        self.grid.addWidget(self.trial_counter, 0, 0, Qt.AlignCenter)
        self.grid.addWidget(self.parameters_container, 0, 0, Qt.AlignCenter)
        self.grid.addWidget(self.push_button1, 1, 0)

        self.trial_counter.hide()
        self.parameters_container.show()

        self.push_button1.setFocus()

        self.show()

    def run(self):

        parameters = {}

        error = 0
        for parameter_name in self.parameters_container.parameters:

            value = self.parameters_container.parameters[parameter_name].get_value()
            if value != "error":

                parameters[parameter_name] = value

            else:
                error = 1
                break

        if error == 1:

            msg = "Bad arguments!"

            QMessageBox().warning(self, "Warning!", msg)

        else:

            print("Interface: Run task.")
            self.parameters_values.put(parameters)
            self.push_button1.setText("Terminate task!")
            # noinspection PyUnresolvedReferences
            self.push_button1.clicked.disconnect()
            # noinspection PyUnresolvedReferences
            self.push_button1.clicked.connect(self.close_task)

            self.parameters_container.hide()

            self.trial_counter.show()
            self.trial_counter.start()

            self.shutdown_event.clear()

            self.timer.start()

    def close_task(self):

        print("Interface: Close task.")

        self.push_button1.setText("Run!")
        # noinspection PyUnresolvedReferences
        self.push_button1.clicked.disconnect()
        # noinspection PyUnresolvedReferences
        self.push_button1.clicked.connect(self.run)

        self.parameters_container.show()

        self.trial_counter.hide()
        self.trial_counter.stop()

        self.timer.stop()
        if not self.shutdown_event.is_set():
            self.shutdown_event.set()

    def check_task_running(self):

        if self.shutdown_event.is_set() and not self.general_shutdown_event.is_set():

            self.close_task()

    def closeEvent(self, event):

        if self.isVisible():

            self.general_shutdown_event.set()
            self.shutdown_event.set()
            self.parameters_values.put(None)
            print("Interface: GENERAL SHUTDOWN.")
