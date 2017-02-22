# -*- coding: utf-8 -*-
from multiprocessing import Event, Queue
from PyQt5 import QtCore
import socket
import errno
import subprocess


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- ABSTRACT CLASS TO COMMUNICATE WITH THE  RASPBERRY PI -------------------- #
# --------------------------------------------------------------------------------------------------------------- #


class Client(object):

    def __init__(self, function, raspi_address):

        self.function = function

        if self.function == "speaker":

            self.server_port = 1555

        else:

            self.server_port = 1556

        self.server_host = raspi_address

        self.socket = self.establish_connection()

    def establish_connection(self):

        while True:

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)

            try:

                sock.connect((self.server_host, self.server_port))
                break

            except socket.error as e:
                print(self.function.capitalize() + ": Error during socket connexion: ", e)
                if e.errno == errno.ECONNREFUSED:
                    sock.close()
                Event().wait(2)

        print(self.function.capitalize() + ": I'm connected.")

        sock.settimeout(None)
        
        return sock

    def close(self):

        self.socket.close()


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- VALVE MANAGER ----------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------- #


class ValveManager(QtCore.QThread):

    def __init__(self, raspi_address='169.254.162.142'):

        super(ValveManager, self).__init__()

        self.valve_queue = Queue()
        self.raspi_address = raspi_address

        self.shutdown = Event()

        self.client = None

    def establish_connection(self):

        self.client = Client(function="speaker", raspi_address=self.raspi_address)

    def run(self):

        print("ValveManager: Running.")

        while not self.shutdown.is_set():

            v = self.valve_queue.get()
            if not self.shutdown.is_set():

                self.client.socket.send("1{}".format(v).encode())

        self.client.close()

        print("ValveManager: DEAD.")

    def open(self, time):

        self.valve_queue.put(time)

    def end(self):

        self.shutdown.set()
        self.valve_queue.put(None)


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- GRIP MANAGER ------------------------------------------------------------ #
# --------------------------------------------------------------------------------------------------------------- #


class GripManager(QtCore.QThread):

    def __init__(self, grip_value, grip_queue, raspi_address='169.254.162.142'):

        super(GripManager, self).__init__()

        self.grip_value = grip_value
        self.grip_queue = grip_queue
        self.raspi_address = raspi_address

        self.client = None

        self.shutdown = Event()

    def establish_connection(self):

        self.client = Client(function="listener", raspi_address=self.raspi_address)

    def run(self):

        print("GripManger: Running.")

        while not self.shutdown.is_set():

            response = self.client.socket.recv(1)
            if response:

                self.grip_value.value = int(response)
                self.grip_queue.put(int(response))

        self.client.close()

        print("GripManager: DEAD.")

    def end(self):

        self.shutdown.set()

# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- SOUND ------------------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------- #


class SoundManager(QtCore.QThread):

    def __init__(self, n_sound_thread=4):

        super().__init__()
        self.sound_queue = Queue()
        self.shutdown = Event()
        self.n_sound_threads = n_sound_thread
        self.sound_threads = []
        for i in range(self.n_sound_threads):

            self.sound_threads.append(SoundPlayer())
            self.sound_threads[i].start()

    def run(self):

        i = 0

        while not self.shutdown.is_set():
            sound = self.sound_queue.get()
            if not self.shutdown.is_set():

                print("Play sound for {} with SoundPlayer {}.".format(sound, i))
                self.sound_threads[i].sound_queue.put(sound)
                if i < self.n_sound_threads-1:
                    i += 1
                else:
                    i = 0

        print("SoundManager: DEAD.")

    def play(self, sound):

        self.sound_queue.put(sound)

    def end(self):

        self.shutdown.set()
        self.sound_queue.put(None)

        for i in range(self.n_sound_threads):
            self.sound_threads[i].end()


class SoundPlayer(QtCore.QThread):

    def __init__(self):

        super().__init__()
        self.sound_queue = Queue()
        self.shutdown = Event()

    def run(self):

        while not self.shutdown.is_set():

            sound = self.sound_queue.get()
            if not self.shutdown.is_set():
                subprocess.call(["afplay", "sounds/{}.wav".format(sound)])

    def end(self):

        self.shutdown.set()
        self.sound_queue.put(None)


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- GRIP TRACKER ------------------------------------------------------------ #
# --------------------------------------------------------------------------------------------------------------- #


class GripTracker(QtCore.QThread):

    def __init__(self, change_queue):

        super().__init__()
        self.go_queue = Queue()
        self.change_queue = change_queue
        self.cancel_signal = True
        self.handling_function = None
        self.shutdown = Event()

    def run(self):

        while not self.shutdown.is_set():

            print("GripTracker: waiting order.")

            msg = self.go_queue.get()
            if not self.shutdown.is_set():

                self.cancel_signal = False

                print("Grip tracker message:", msg)

                args = self.change_queue.get()

                if not self.cancel_signal:
                    print("GripTracker: args =", args)
                    print("GripTracker: CALL.")
                    self.handling_function()

    def launch(self, handling_function, msg=""):

        while not self.change_queue.empty():
            self.change_queue.get()

        self.handling_function = handling_function
        self.go_queue.put(msg)

    def cancel(self):

        print("GripTracker: CANCEL.")
        self.cancel_signal = True
        self.change_queue.put(None)

    def end(self):

        print("GripTracker: END.")
        self.shutdown.set()
        self.cancel_signal = True
        self.change_queue.put(None)
        self.go_queue.put(None)
