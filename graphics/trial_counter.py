from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QSpacerItem


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