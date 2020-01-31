# coding=utf-8
import sys
from multiprocessing import Queue, Value, Event

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from graphics.interface import Interface
from graphics.generic import Communicant
from task.experimentalist import Manager
# from utils.utils import git_report


if __name__ == "__main__":

    # Make a log of git status
    # git_report()

    # Start graphic processes

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("textures/monkey.png"))

    queues = {
        "manager": Queue(),
        "interface": Queue(),
        "grip_queue": Queue(),
        "grip_value": Value('i', 0)
    }

    shutdown = Event()
    communicant = Communicant()

    interface = Interface(queues=queues, communicant=communicant, shutdown=shutdown)

    # Start process that will handle events
    experimentalist = Manager(
        queues=queues,
        communicant=communicant,
        shutdown=shutdown
    )

    experimentalist.start()
    sys.exit(app.exec_())
