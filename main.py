# coding=utf-8
from multiprocessing import Queue
from PyQt5.QtWidgets import QApplication
import sys
from task.game_window import GameWindow
from task.interface import Interface
from task.experimentalist import Experimentalist


if __name__ == "__main__":

    # Start graphic processes

    app = QApplication(sys.argv)

    graphic_queue = Queue()

    interface_window = Interface(queue=graphic_queue)
    game_window = GameWindow(queue=graphic_queue)

    # Start process that will handle events
    experimentalist = Experimentalist(
        game_window=game_window,
        interface_window=interface_window,
        graphic_queue=graphic_queue
    )

    experimentalist.start()

    sys.exit(app.exec_())
