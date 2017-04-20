from multiprocessing import Event, Queue
from threading import Thread
import socket
import errno

from utils.utils import log


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- ABSTRACT CLASS TO COMMUNICATE WITH THE  RASPBERRY PI -------------------- #
# --------------------------------------------------------------------------------------------------------------- #


class Client(object):

    def __init__(self, func, rpi_ip_address):

        self.function = func

        if self.function == "speaker":

            self.server_port = 1555

        else:

            self.server_port = 1556

        self.server_host = rpi_ip_address

        self.socket = None

    def establish_connection(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)

        try:

            sock.connect((self.server_host, self.server_port))
            sock.settimeout(None)
            log("I'm connected.", self.function.capitalize())
            self.socket = sock
            return 1

        except socket.error as e:
            log("Error during socket connexion: {}.".format(e), self.function.capitalize())
            if e.errno == errno.ECONNREFUSED:
                sock.close()
            return 0

    def close(self):

        self.socket.close()


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- VALVE MANAGER ----------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------- #


class ValveManager(Thread):

    name = "ValveManager"

    def __init__(self, rpi_ip_address):

        super().__init__()

        self.rpi_ip_address = rpi_ip_address

        self.valve_queue = Queue()
        self.shutdown = Event()

        self.client = Client(func="speaker", rpi_ip_address=self.rpi_ip_address)

    def establish_connection(self):

        return self.client.establish_connection()

    def run(self):

        log("Running.", self.name)

        while not self.shutdown.is_set():

            v = self.valve_queue.get()
            if not self.shutdown.is_set():

                self.client.socket.send("{:4d}".format(v).encode())

        # self.client.socket.send("")
        self.client.close()

        log("DEAD.", self.name)

    def open(self, time):

        self.valve_queue.put(time)

    def end(self):

        self.shutdown.set()
        self.valve_queue.put(None)


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- GRIP MANAGER ------------------------------------------------------------ #
# --------------------------------------------------------------------------------------------------------------- #


class GripManager(Thread):

    name = "GripManager"

    def __init__(self, grip_value, grip_queue, rpi_ip_address):

        super().__init__()

        self.grip_value = grip_value
        self.grip_queue = grip_queue
        self.rpi_ip_address = rpi_ip_address

        self.client = Client(func="listener", rpi_ip_address=self.rpi_ip_address)

        self.shutdown = Event()

    def establish_connection(self):

        return self.client.establish_connection()

    def run(self):

        log("Running.", self.name)

        while not self.shutdown.is_set():

            response = self.client.socket.recv(1)
            if response:

                if int(response) != self.grip_value.value:
                    self.grip_queue.put(int(response))

                self.grip_value.value = int(response)

        self.client.close()

        log("DEAD.", self.name)

    def end(self):

        self.shutdown.set()


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- GRIP TRACKER ------------------------------------------------------------ #
# --------------------------------------------------------------------------------------------------------------- #


class GripTracker(Thread):

    name = "GripTracker"

    def __init__(self, change_queue, message_queue):

        super().__init__()
        self.go_queue = Queue()
        self.change_queue = change_queue
        self.message_queue = message_queue
        self.cancel_signal = Event()
        self.shutdown = Event()

    def run(self):

        while not self.shutdown.is_set():

            log("Waiting order.", self.name)
            msg = self.go_queue.get()

            if not self.shutdown.is_set():
                log("Received order to deliver message if change in grip state: '{}'.".format(msg), self.name)
                args = self.change_queue.get()

                if not self.cancel_signal.is_set():
                    log("Received event in change queue: '{}'.".format(args), self.name)
                    self.message_queue.put(("grip_tracker", msg))

        log("I'm DEAD.", self.name)

    def launch(self, msg):

        while not self.change_queue.empty():
            self.change_queue.get()
        self.cancel_signal.clear()
        self.go_queue.put(msg)

    def cancel(self):

        log("CANCEL.", self.name)
        self.cancel_signal.set()
        self.change_queue.put(None)

    def end(self):

        log("END.", self.name)
        self.shutdown.set()
        self.cancel_signal.set()
        self.change_queue.put(None)
        self.go_queue.put(None)

    def is_cancelled(self):

        return self.cancel_signal.is_set()


# --------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------- TIMER ------------------------------------------------------------ #
# --------------------------------------------------------------------------------------------------------------- #


class Timer(Thread):

    def __init__(self, message_queue, name):

        super().__init__()
        self.name = "Timer{}".format(name.capitalize())
        self.go_queue = Queue()
        self.message_queue = message_queue
        self.cancel_signal = Event()
        self.wait_signal = Event()
        self.shutdown = Event()

    def run(self):

        while not self.shutdown.is_set():

            log("Waiting order.", self.name)
            msg, time, kwargs = self.go_queue.get()

            if not self.shutdown.is_set():
                log("Received order to deliver message '{}' with kwargs '{}' after {} seconds."
                    .format(msg, kwargs, time), self.name)
                self.wait_signal.wait(timeout=time)

                if not self.cancel_signal.is_set():
                    log("Time elapsed.", self.name)
                    self.message_queue.put(("timer", msg, kwargs))

        log("I'm DEAD.", self.name)

    def launch(self, msg, time, kwargs=None):

        self.cancel_signal.clear()
        self.wait_signal.clear()
        self.go_queue.put((msg, time, kwargs))

    def cancel(self):

        log("CANCEL.", self.name)
        self.cancel_signal.set()
        self.wait_signal.set()

    def end(self):

        log("END.", self.name)
        self.shutdown.set()
        self.cancel_signal.set()
        self.wait_signal.set()
        self.go_queue.put((None, None, None))

    def is_cancelled(self):

        return self.cancel_signal.is_set()
