from threading import Thread, Event, Lock
import socket
import RPi.GPIO as GPIO
import serial as sr
from datetime import datetime as dt


class Master:

    def __init__(self):

        self.go_event = Event()
        self.shutdown_event = Event()
        self.ear = Listener(self.go_event, self.shutdown_event)
        self.mouth = Speaker(self.go_event, self.shutdown_event)

        self.go_event.set()

        self.ear.start()
        self.mouth.start()

        try:

            while self.ear.isAlive() or self.mouth.isAlive():
                self.ear.join(timeout=1.0)
                self.mouth.join(timeout=1.0)

        except (KeyboardInterrupt, SystemExit):

            self.shutdown_event.set()


class Pump:

    def __init__(self):

        self.serial_port = "/dev/ttyUSB0"
        self.ser = sr.Serial(self.serial_port)

    def launch(self, open_time):

        a = time()
        self.ser.write("S11")
        dummy_event = Event()
        dummy_event.wait(timeout=open_time/1000.)
        self.ser.write("S10")
        b = time()
        print "Open time of pump", b-a

    def close(self):

        self.ser.close()


class Detector:

    def __init__(self):

        self.gpio_in = 26
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_in, GPIO.IN)

    def detect(self):

        return 1 - GPIO.input(self.gpio_in)

    @staticmethod
    def close():

        GPIO.cleanup()


class Server(Thread):

    def __init__(self, function):

        Thread.__init__(self)

        self.function = function

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.client = None

        if self.function == "listen":
            self.client_port = 1555
        else:
            self.client_port = 1556

    def close(self):

        self.sock.close()

    def accept_connection(self):

        self.sock.bind(('', self.client_port))

        self.sock.listen(1)
        d = dt.now()
        print "{h:02d}:{m:02d}:{s:02d}:{ms:02d} Wait for connection..."\
            .format(h=d.hour, m=d.minute, s=d.second, ms=d.microsecond)
        self.client, address = self.sock.accept()
        d = dt.now()
        print "{h:02d}:{m:02d}:{s:02d}:{ms:02d} {a} connected."\
            .format(h=d.hour, m=d.minute, s=d.second, ms=d.microsecond, a=address)


class Speaker(Server):

    def __init__(self, go_event, shutdown_event):

        super(Speaker, self).__init__(function="speak")
        self.go_event = go_event
        self.shutdown_event = shutdown_event
        self.detector = Detector()
        self.detector_state = self.detector.detect()

    def run(self):

        d = dt.now()
        print "{h:02d}:{m:02d}:{s:02d}:{ms:02d} Beginning of raspi speaker."\
            .format(h=d.hour, m=d.minute, s=d.second, ms=d.microsecond)
        self.accept_connection()

        self.speak()
        self.close()
        self.detector.close()
        d = dt.now()
        print "{h:02d}:{m:02d}:{s:02d}:{ms:02d}  End of rapspi speaker."\
            .format(h=d.hour, m=d.minute, s=d.second, ms=d.microsecond)

    def speak(self):

        self.detector_state = self.detector.detect()
        self.client.send(str(self.detector_state))

        while not self.shutdown_event.is_set():

            self.go_event.wait()

            if not self.shutdown_event.is_set():

                new_detector_state = self.detector.detect()

                if self.detector_state != new_detector_state:

                    d = dt.now()

                    print "{h:02d}:{m:02d}:{s:02d}:{ms:02d}  I (raspi speaker) have detected " \
                          "a changement in detector state.\n" \
                          "I inform Mac of the change. The new state is {state}"\
                        .format(h=d.hour, m=d.minute, s=d.second, ms=d.microsecond, state=new_detector_state)

                    self.client.send(str(new_detector_state))
                    self.detector_state = new_detector_state
            else:
                pass


class Listener(Server):

    def __init__(self, go_event, shutdown_event):

        super(Listener, self).__init__(function="listen")
        self.lock = Lock()
        self.go_event = go_event
        self.shutdown_event = shutdown_event
        self.pump = Pump()

    def run(self):

        d = dt.now()
        print "{h:02d}:{m:02d}:{s:02d}:{ms:02d} Beginning of raspi listener."\
            .format(h=d.hour, m=d.minute, s=d.second, ms=d.microsecond)
        self.accept_connection()

        self.listen()
        self.close()
        self.pump.close()
        d = dt.now()
        print "{h:02d}:{m:02d}:{s:02d}:{ms:02d} End of raspi listener."\
            .format(h=d.hour, m=d.minute, s=d.second, ms=d.microsecond)

    def listen(self):

        while not self.shutdown_event.is_set():

            response = self.client.recv(255)

            if response:
                if response[0] == "1":
                    open_time = int(float(response[1:]))

                    d = dt.now()
                    print "{h:02d}:{m:02d}:{s:02d}:{ms:02d}  " \
                          "I (raspi listener) have received the order to deliver water."\
                        .format(h=d.hour, m=d.minute, s=d.second, ms=d.microsecond, r=response)

                    with self.lock:

                        self.go_event.clear()
                        self.pump.launch(open_time)
                        self.go_event.set()
                elif response == "shut_up":

                    print "{h:02d}:{m:02d}:{s:02d}:{ms:02d}  " \
                          "I (raspi listener) have received the order to shut up."\

                    self.go_event.set()
                    self.shutdown_event.set()




if __name__ == "__main__":

    while True:

        Master()
