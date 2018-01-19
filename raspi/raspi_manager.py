import serial as sr
from multiprocessing import Event, Process, Queue
from time import time
import socket
import RPi.GPIO as GPIO


class TtlSignal(Process):

    def __init__(self):

        super().__init__()
        self.queue = Queue()
        self.shutdown = Event()

        self.gpio_out = 19
        GPIO.setup(self.gpio_out, GPIO.OUT)
        GPIO.output(self.gpio_out, GPIO.LOW)

        self.start()

    def _send(self):

        GPIO.output(self.gpio_out, GPIO.HIGH)
        Event().wait(0.02)
        GPIO.output(self.gpio_out, GPIO.LOW)

    def run(self):

        while not self.shutdown.is_set():

            order = self.queue.get()
            if order:
                self._send()

    def send(self):

        self.queue.put(True)

    def close(self):
        self.shutdown.set()
        self.queue.put(None)


class Valve:

    def __init__(self):

        self.serial_port = "/dev/ttyUSB0"
        self.ser = sr.Serial(self.serial_port)

        self.timer = Event()

    def launch(self, open_time):

        a = time()
        self.ser.write("S11".encode())
        self.timer.wait(timeout=open_time/1000.)
        self.ser.write("S10".encode())
        b = time()
        print("Open time of valve:", b-a)

    def close(self):

        self.ser.close()


class Grip:

    def __init__(self):

        self.gpio_in = 26
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_in, GPIO.IN)

    def detect(self):

        grip_state = 1 - GPIO.input(self.gpio_in)
        print("Grip state:", grip_state)
        return grip_state


def main():

    grip = Grip()
    valve = Valve()
    ttl_signal = TtlSignal()

    host = ''  # Symbolic name meaning all available interfaces
    port = 1556  # Arbitrary non-privileged port

    try:

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

            s.bind((host, port))
            s.listen(1)
            while True:

                print("Waiting for connection...")
                conn, addr = s.accept()

                with conn:

                    print("Connected by '{}'.".format(addr))
                    while True:

                        try:
                            data = conn.recv(5)  # Go signal
                            if data:
                                data = data.decode()
                                if data[0] == "v":
                                    aperture = int(data[1:].replace("*", ""))
                                    valve.launch(aperture)

                                elif data[0] == "g":
                                    detector_state = grip.detect()
                                    conn.send("{}".format(detector_state).encode())

                                elif data[0] == "s":
                                    ttl_signal.send()

                                else:
                                    print("Message not understood: '{}'.".format(data))
                            else:
                                print("No message.")
                                break

                        except Exception as e:
                            print(e)
                            break

    except (SystemExit, KeyboardInterrupt, Exception) as e:
        print("Got exception '{}' and will exit.".format(e))

        valve.close()
        ttl_signal.close()

        GPIO.cleanup()


if __name__ == "__main__":

    main()
