# -*- coding: utf-8 -*-
from multiprocessing import Event
from PyQt5.QtCore import Qt
from threading import Thread
import socket
import errno
from pexpect import pxssh
import subprocess


raspi_address = '169.254.162.142'


class FakeValveManager(Thread):

    def __init__(self, valve_opening, shutdown_event):

        super(FakeValveManager, self).__init__()
        self.valve_opening = valve_opening
        self.shutdown_event = shutdown_event

    def run(self):

        while not self.shutdown_event.is_set():

            v = self.valve_opening.get()
            if v:
                print("Valve opening for ", v, "milli seconds.")
                Event().wait(v/1000.)

        print("FakeValveManager: DEAD.")


class FakeGripManager(Thread):

    def __init__(self, keyboard_queue, grip_state, grip_change, shutdown_event):

        super(FakeGripManager, self).__init__()
        self.keyboard_queue = keyboard_queue
        self.shutdown_event = shutdown_event
        self.grip_state = grip_state
        self.grip_change = grip_change

    def run(self):

        while not self.shutdown_event.is_set():

            try:

                k = self.keyboard_queue.get()
                if k and k[1] == Qt.Key_P:

                    if k[0] == 1:
                        self.grip_state.value = 1
                        self.grip_change.put(1)
                    else:
                        self.grip_state.value = 0
                        self.grip_change.put(0)
            except EOFError:
                pass

        print("FakeGripManager: DEAD.")


class Client(object):

    def __init__(self, function):

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


class ValveManager(Thread, Client):

    def __init__(self, valve_opening, shutdown_event):

        super(ValveManager, self).__init__()
        self.client = Client(function="speaker")
        self.valve_opening = valve_opening
        self.shutdown_event = shutdown_event

    def run(self):

        self.client.establish_connection()

        while not self.shutdown_event.is_set():

            v = self.valve_opening.get()
            if v:
                self.client.sock.send("1{}".format(v).encode())
                # print "Valve opening time: ", v

        self.client.sock.send("shut_up".encode())  # Send the raspi to shut_up and free GripManager
        self.client.close()

        print("ValveManager: DEAD.")


class GripManager(Thread):

    def __init__(self, grip_state, grip_change, shutdown_event):

        super(GripManager, self).__init__()
        self.client = Client(function="listener")
        self.shutdown_event = shutdown_event
        self.grip_state = grip_state
        self.grip_change = grip_change

    def run(self):

        self.client.establish_connection()

        while not self.shutdown_event.is_set():

            response = self.client.sock.recv(255)
            if response:
                self.grip_state.value = int(response)
                self.grip_change.put(int(response))

        self.client.close()

        print("GripManager: DEAD.")


class ConnectionToRaspi(object):

    def __init__(self):

        print("Setting up the raspi, please be patient!")
        print("Trying to connect to the raspi...")

        while True:

            self.c = pxssh.pxssh()

            try:
                connect_to_pi = self.c.login(raspi_address, "pi", "raspberry")
                if connect_to_pi:
                    print("Successfully connected to the raspi.")
                    break

            except Exception as e:

                print("Error during connection to raspi:"), e
                print("Trying again to connect...")
                Event().wait(3)

        self.launch_server()  # Launch the server program on Raspberry Pi.

    def launch_server(self):

        self.c.sendline("python ~/Desktop/raspi.py")
        self.c.prompt(timeout=1)

        print("Server launched.")


class Sound(Thread):

    def __init__(self, sound_instruction, shutdown_event):

        super(Sound, self).__init__()
        self.sound_instruction = sound_instruction
        self.shutdown = shutdown_event
        self.n_sound_threads = 4
        self.sound_threads = []
        for i in range(self.n_sound_threads):

            self.sound_threads.append(SoundPlayer(shutdown=self.shutdown))
            self.sound_threads[i].start()

    def run(self):

        i = 0

        while not self.shutdown.is_set():
            instruction = self.sound_instruction.get()
            if not self.shutdown.is_set():
                # print "Play sound for {}.".format(instruction)
                print("Play sound for {} with SoundPlayer {}.".format(instruction, i))
                self.sound_threads[i].play(instruction)
                if i < self.n_sound_threads-1:
                    i += 1
                else:
                    i = 0
            else:
                for i in range(self.n_sound_threads):
                    self.sound_threads[i].launch.set()

        print("SoundManager: DEAD.")


class SoundPlayer(Thread):

    def __init__(self, shutdown):

        Thread.__init__(self)
        self.sound = None
        self.shutdown = shutdown
        self.launch = Event()

    def play(self, sound):

        self.sound = sound

        self.launch.set()

    def run(self):

        while not self.shutdown.is_set():

            self.launch.wait()
            if not self.shutdown.is_set():
                subprocess.call(["afplay", "sounds/{}.wav".format(self.sound)])
                self.launch.clear()
