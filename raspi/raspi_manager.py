import serial as sr
from multiprocessing import Event
from time import time
import socket
import RPi.GPIO as GPIO


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

        return 1 - GPIO.input(self.gpio_in)

    @staticmethod
    def close():

        GPIO.cleanup()


def main():

    grip = Grip()
    valve = Valve()

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

                            if data[0] == "v":
                                aperture = int(data[1:].replace("*", ""))
                                valve.launch(aperture)

                            elif data[0] == "g":
                                detector_state = grip.detect()
                                conn.send("{}".format(detector_state).encode())

                            else:
                                raise Exception("Message not understood.")

                        except socket.error as exc:
                            print("Caught exception socket.error: '{}'.".format(exc))
                            break

    except (SystemExit, KeyboardInterrupt, Exception):

        print("Exit.")
        grip.close()
        valve.close()


if __name__ == "__main__":

    main()
