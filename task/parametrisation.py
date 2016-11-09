from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, \
    QRadioButton, QCheckBox
from collections import OrderedDict
import json


class ParametersContainer(QWidget):

    def __init__(self):

        QWidget.__init__(self)

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.parameters = OrderedDict()

        with open("parameters/parameters.json") as param_file:

            param = json.load(param_file)

        self.parameters["initial_stock"] = \
            Parameter(
                text="Initial stock", initial_value=param["initial_stock"],
                value_range=[0, 20])

        self.parameters["trials_per_block"] = \
            Parameter(
                text="Trials per block", initial_value=param["trials_per_block"],
                value_range=[1, 20])

        self.parameters["reward_time"] = \
            Parameter(
                text="Reward time (ms)", initial_value=param["reward_time"],
                value_range=[1000, 100000])

        self.parameters["valve_opening_time"] = \
            Parameter(
                text="Valve opening time (ms)", initial_value=param["valve_opening_time"],
                value_range=[1, 10000])

        self.parameters["fixation_time"] = \
            MinMaxParameter(
                text="Fixation time (ms)", initial_value_min=param["fixation_time"][0],
                initial_value_max=param["fixation_time"][1],
                value_range_min=[1, 100000],
                value_range_max=[1, 100000])

        self.parameters["max_decision_time"] = \
            Parameter(
                text="Max decision time (ms)", initial_value=param["max_decision_time"],
                value_range=[1, 100000])

        self.parameters["max_return_time"] = \
            Parameter(text="Max return time (ms)", initial_value=param["max_return_time"],
                      value_range=[1, 100000])

        self.parameters["result_display_time"] = \
            Parameter(text="Result display time (ms)", initial_value=param["result_display_time"],
                      value_range=[1, 100000])

        self.parameters["inter_trial_time"] = \
            MinMaxParameter(
                text="Inter-trial time (ms)", initial_value_min=param["inter_trial_time"][0],
                initial_value_max=param["inter_trial_time"][1],
                value_range_min=[1, 100000],
                value_range_max=[1, 100000])

        self.parameters["punishment_time"] = \
            Parameter(text="Punishment time (ms)", initial_value=param["punishment_time"],
                      value_range=[1, 100000])

        self.parameters["monkey"] = \
            RadioParameter(text="Monkey", text_radio1="Havane", text_radio2="Gladys")

        self.parameters["save"] = \
            CheckParameter(text="Save results", checked=param["save"])

        self.parameters["fake"] = \
            CheckParameter(text="Use fake grip and reward system", checked=param["fake"])

        for i, p in enumerate(self.parameters.keys()):

            self.parameters[p].add_to_grid(grid=self.grid, line=i)

    def get_parameters(self):

        parameters = {}

        error = 0
        for parameter_name in self.parameters:

            value = self.parameters[parameter_name].get_value()
            if value != "error":

                parameters[parameter_name] = value

            else:
                error = 1
                break
        return error, parameters


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

    def __init__(self, text, checked=True):

        self.label = QLabel(text)
        self.check_box = QCheckBox()

        self.check_box.setChecked(checked)

    def get_value(self):

        return self.check_box.isChecked()

    def add_to_grid(self, grid, line):

        grid.addWidget(self.label, line, 0)
        grid.addWidget(self.check_box, line, 1)
