from multiprocessing import Queue
from threading import Thread, Event
from datetime import datetime as dt
import socket
import errno

from utils.utils import log


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- ABSTRACT CLASS TO COMMUNICATE WITH THE  RASPBERRY PI -------------------- #
# --------------------------------------------------------------------------------------------------------------- #


class Client(object):

    def __init__(self, ip_address, port):

        self.server_address = (ip_address, port)
        self.socket = None
        self.connected = False

    def establish_connection(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)

        try:

            sock.connect(self.server_address)
            sock.settimeout(None)
            log("I'm connected.", "RaspiManager")
            self.socket = sock
            self.connected = True
            return 1

        except socket.error as e:
            log("Error during socket connexion: {}.".format(e), "RaspiManager")
            if e.errno == errno.ECONNREFUSED:
                sock.close()
            return 0

    def send(self, string):

        self.socket.send('{:*<5}'.format(string).encode())

    def recv(self):

        return self.socket.recv(1).decode()

    def close(self):

        self.socket.close()

    def is_connected(self):

        return self.connected


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- VALVE MANAGER ----------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------- #


class ValveManager(Thread):

    name = "ValveManager"

    def __init__(self, client):

        super().__init__()

        self.valve_queue = Queue()
        self.shutdown = Event()

        self.client = client

    def run(self):

        log("Running.", self.name)

        while not self.shutdown.is_set():

            v = self.valve_queue.get()
            if not self.shutdown.is_set():

                self.client.send("v{:4d}".format(v))

        self.client.close()

        log("DEAD.", self.name)

    def open(self, time):

        self.valve_queue.put(time)

    def end(self):

        self.shutdown.set()
        self.valve_queue.put(None)


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- TTL MANAGER ------------------------------------------------------------ #
# --------------------------------------------------------------------------------------------------------------- #


class TtlManager(Thread):

    name = "TtlManager"

    def __init__(self, client):

        super().__init__()

        self.client = client

        self.ttl_queue = Queue()
        self.shutdown = Event()

    def run(self):

        log("Running.", self.name)

        while not self.shutdown.is_set():

            self.ttl_queue.get()
            if not self.shutdown.is_set():

                self.client.send("s")

        self.client.close()

        log("DEAD.", self.name)

    def end(self):

        self.shutdown.set()
        self.ttl_queue.put(None)

    def send_signal(self):

        self.ttl_queue.put(True)


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- GRIP MANAGER ------------------------------------------------------------ #
# --------------------------------------------------------------------------------------------------------------- #


class GripManager(Thread):

    name = "GripManager"

    def __init__(self, grip_value, grip_queue, client):

        super().__init__()

        self.grip_value = grip_value
        self.grip_queue = grip_queue

        self.client = client

        self.track_signal = Event()
        self.shutdown = Event()

    def run(self):

        log("Running.", self.name)

        while not self.shutdown.is_set():

            self.client.send("g")  # Go signal
            response = self.client.recv()
            if response:

                response = int(response)

                if response != self.grip_value.value:
                    self.grip_queue.put(response)

                self.grip_value.value = response

            Event().wait(0.01)  # Precision of 10 ms for the grip

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
        self.waiting = Event()
        self.cancelled = Event()
        self.running = Event()

    def run(self):

        while not self.shutdown.is_set():

            log("Waiting order.", self.name)
            msg = self.go_queue.get()
            self.running.set()

            if not self.shutdown.is_set():

                log("If change in grip state, I will deliver message '{}'.".format(msg), self.name)

                self.waiting.set()
                args = self.change_queue.get()
                self.waiting.clear()

                if not self.cancel_signal.is_set():

                    log("Received event in change queue: '{}'.".format(args), self.name)
                    self.message_queue.put(("grip_tracker", msg))

                else:
                    log("Cancelled.", self.name)
                    self.cancelled.set()

        log("I'm DEAD.", self.name)

    def launch(self, msg):

        while not self.change_queue.empty():
            self.change_queue.get()

        self.cancel_signal.clear()
        self.go_queue.put(msg)
        self.running.wait()
        self.running.clear()

    def cancel(self):

        log("CANCEL.", self.name)

        self.cancel_signal.set()

        if self.waiting.is_set():
            self.change_queue.put(None)
            self.cancelled.wait()
            self.cancelled.clear()
        else:
            log("I was not running.", self.name)

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

    name = "Timer"

    def __init__(self, message_queue):

        super().__init__()

        self.message_queue = message_queue

        self.go_queue = Queue()

        self.cancel_signal = Event()
        self.wait_signal = Event()
        self.cancelled = Event()
        self.shutdown = Event()
        self.waiting = Event()
        self.running = Event()

        self.msg, self.ts = None, None

    def run(self):

        while not self.shutdown.is_set():

            log("Waiting order.", self.name)

            msg, time = self.go_queue.get()
            self.running.set()

            if not self.shutdown.is_set():

                log("ORDER message '{}' with ts '{}'.".format(msg, self.ts), self.name)

                self.waiting.set()
                self.wait_signal.wait(timeout=time)
                self.waiting.clear()

                log("RELEASED WITH MESSAGE '{}' with ts '{}'.".format(msg, self.ts), self.name)

                if not self.cancel_signal.is_set():
                    log("RUN message '{}' with ts '{}'.".format(msg, self.ts), self.name)
                    self.message_queue.put(("timer", msg, self.ts))

                else:
                    log("CANCELLED message '{}' with ts '{}'.".format(msg, self.ts), self.name)
                    self.cancelled.set()

        log("I'm DEAD.", self.name)

    def launch(self, msg, time, debug=None):

        ts = dt.utcnow()
        self.msg, self.ts = msg, ts

        log("LAUNCH with message '{}' and ts '{}' /// DEBUG: {}.".format(self.msg, self.ts, debug), self.name)

        self.cancel_signal.clear()
        self.wait_signal.clear()
        self.go_queue.put((msg, time))
        self.running.wait()
        self.running.clear()

    def cancel(self, debug=None):

        log("CANCEL with message '{}' and ts '{}' /// DEBUG: {}.".format(self.msg, self.ts, debug), self.name)
        self.cancel_signal.set()

        if self.waiting.is_set():

            self.wait_signal.set()
            self.cancelled.wait()
            self.cancelled.clear()

    def end(self):

        log("END.", self.name)
        self.shutdown.set()
        self.cancel_signal.set()
        self.wait_signal.set()
        self.go_queue.put((None, None))

    def is_cancelled(self):

        return self.cancel_signal.is_set()


class GaugeAnimation(Thread):

    name = "GaugeAnimation"
    message = "set_gauge_quantity"

    def __init__(self, message_queue):

        super().__init__()

        self.message_queue = message_queue

        self.go_queue = Queue()

        self.cancel_signal = Event()
        self.wait_signal = Event()
        self.cancelled = Event()
        self.shutdown = Event()
        self.waiting = Event()
        self.running = Event()

        self.msg, self.ts = None, None

    def run(self):

        while not self.shutdown.is_set():

            log("Waiting order.", self.name)

            kwargs = self.go_queue.get()
            self.running.set()

            if not self.shutdown.is_set():

                # '+2' allows to have a short time before the beginning of the sequence and a short time at the end
                time_per_unity = kwargs["total_time"] / (kwargs["maximum"] + 2)
                log("Time per unity: {}, Total time: {}, Maximum x: {}".format(time_per_unity, kwargs["total_time"],
                                                                kwargs["maximum"]), self.name)

                for i, j in enumerate(kwargs["sequence"]):

                    self.waiting.set()
                    self.wait_signal.wait(timeout=time_per_unity)
                    self.waiting.clear()

                    log("RELEASED.", self.name)

                    if not self.cancel_signal.is_set():
                        log("RUN for the {}st/nd time.".format(i), self.name)

                        kwargs = {
                            "quantity": j,
                            "sound": kwargs["sound"],
                            "water": kwargs["water"]
                        }

                        self.message_queue.put(("gauge_animation", self.message, kwargs))
                    else:
                        break

                log("CANCELLED / FINISHED.", self.name)
                self.cancelled.set()

        log("I'm DEAD.", self.name)

    def launch(self, **kwargs):

        log("LAUNCH", self.name)

        self.cancel_signal.clear()
        self.wait_signal.clear()
        self.go_queue.put(kwargs)
        self.running.wait()
        self.running.clear()

    def cancel(self, debug=None):

        log("CANCEL with message '{}' and ts '{}' /// DEBUG: {}.".format(self.msg, self.ts, debug), self.name)
        self.cancel_signal.set()

        if self.waiting.is_set():

            self.wait_signal.set()
            self.cancelled.wait()
            self.cancelled.clear()

    def end(self):

        log("END.", self.name)
        self.shutdown.set()
        self.cancel_signal.set()
        self.wait_signal.set()
        self.go_queue.put(None)

    def is_cancelled(self):

        return self.cancel_signal.is_set()