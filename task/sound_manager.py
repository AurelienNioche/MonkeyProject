from threading import Thread
from multiprocessing import Queue, Event
import subprocess

from utils.utils import log


class SoundManager(Thread):

    name = "SoundManager"

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

                log("Play sound for {} with SoundPlayer {}.".format(sound, i), self.name)
                self.sound_threads[i].sound_queue.put(sound)
                if i < self.n_sound_threads-1:
                    i += 1
                else:
                    i = 0

        log("DEAD.", self.name)

    def play(self, sound):

        self.sound_queue.put(sound)

    def end(self):

        self.shutdown.set()
        self.sound_queue.put(None)

        for i in range(self.n_sound_threads):
            self.sound_threads[i].end()


class SoundPlayer(Thread):

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