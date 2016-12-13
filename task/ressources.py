# -*- coding: utf-8 -*-
from multiprocessing import Event, Queue
from PyQt5 import QtCore
import socket
import errno
from pexpect import pxssh
import subprocess


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- CONNECTION TO RASPBERRY PI ---------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------- #


class ConnectionToRaspi(object):

    def __init__(self, raspi_address='169.254.162.142'):

        self.connected = 0
        self.raspi_address = raspi_address
        self.c = None

    def connect(self):

        print("ConnectionToRaspi: Setting up the raspi, please be patient!")
        print("ConnectionToRaspi: Trying to connect to the raspi...")

        while True:

            self.c = pxssh.pxssh()
            self.c.force_password = True

            try:
                print("ConnectionToRaspi: Try to login.")
                connect_to_pi = self.c.login(self.raspi_address, "pi", "raspberry", login_timeout=1)
                if connect_to_pi:
                    print("ConnectionToRaspi: Successfully connected to the raspi.")
                    break

            except Exception as e:

                print("ConnectionToRaspi: Error during connection to raspi:", e)
                print("ConnectionToRaspi: Trying again to connect...")
                Event().wait(1)

        # Launch the server program on Raspberry Pi.
        self.c.sendline("python ~/Desktop/raspi.py")

        print("ConnectionToRaspi: Server launched.")
        self.connected = 1

    def is_connected(self):

        return self.connected

    def end(self):

        if self.connected:
            self.c.sendline("\x03")
            self.c.prompt(timeout=1)
            print("ConnectionToRaspi:", self.c.before)
            self.connected = 0
            self.c.logout()
            self.c.close()


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

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def establish_connection(self):

        error = 0

        while True:

            try:
                self.sock.connect((self.server_host, self.server_port))
                break

            except socket.error as e:
                print(self.function.capitalize() + ": Error during socket connexion: ", e)
                if e.errno == errno.ECONNREFUSED:
                    self.sock.close()
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                Event().wait(2)
                error += 1
        if error > 0:

            print(self.function.capitalize() + ": Errors encountered but problems solved.")

        print(self.function.capitalize() + ": I'm connected.")

    def close(self):

        self.sock.close()


# --------------------------------------------------------------------------------------------------------------- #
# ------------------------------------- VALVE MANAGER ----------------------------------------------------------- #
# --------------------------------------------------------------------------------------------------------------- #


class ValveManager(QtCore.QThread):

    def __init__(self, raspi_address='169.254.162.142'):

        super(ValveManager, self).__init__()

        self.valve_queue = Queue()
        self.raspi_address = raspi_address

        self.shutdown = Event()

    def run(self):

        client = Client(function="speaker", raspi_address=self.raspi_address)

        client.establish_connection()

        print("ValveManager: Running.")

        while not self.shutdown.is_set():

            v = self.valve_queue.get()
            if not self.shutdown.is_set():

                client.sock.send("1{}".format(v).encode())
                # print "Valve opening time: ", v

        client.sock.send("shut_up".encode())  # Send the raspi to shut_up and free GripManager
        client.close()

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

        self.shutdown = Event()

    def run(self):

        client = Client(function="listener", raspi_address=self.raspi_address)

        client.establish_connection()

        print("GripManger: Running.")

        while not self.shutdown.is_set():

            response = client.sock.recv(255)
            if response:

                self.grip_value.value = int(response)
                self.grip_queue.put(int(response))

        client.close()

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
                # print "Play sound for {}.".format(instruction)
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
