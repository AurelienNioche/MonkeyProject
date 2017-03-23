# coding=utf-8
from multiprocessing import Queue
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import sys

from task.game_window import GameWindow
from task.interface import Interface
from task.experimentalist import Experimentalist
from utils.utils import git_report


if __name__ == "__main__":

    # Make a log of git status
    git_report()

    # Start graphic processes

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("textures/monkey.png"))

    graphic_queue = Queue()

    interface_window = Interface(queue=graphic_queue)
    game_window = GameWindow(queue=graphic_queue, textures_folder="textures")

    # Start process that will handle events
    experimentalist = Experimentalist(
        game_window=game_window,
        interface_window=interface_window,
        graphic_queue=graphic_queue
    )

    experimentalist.start()
    sys.exit(app.exec_())
