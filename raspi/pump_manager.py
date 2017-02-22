import serial as sr
from multiprocessing import Event
from time import time
import socket


class Pump:

    def __init__(self):

        self.serial_port = "/dev/ttyUSB0"
        self.ser = sr.Serial(self.serial_port)

    def launch(self, open_time):

        a = time()
        self.ser.write("S11".encode())
        Event().wait(timeout=open_time/1000.)
        self.ser.write("S10".encode())
        b = time()
        print("Open time of pump:", b-a)

    def close(self):

        self.ser.close()


def main():

    pump = Pump()

    host = ''  # Symbolic name meaning all available interfaces
    port = 1555  # Arbitrary non-privileged port
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen(1)
            while True:
                conn, add = s.accept()
                with conn:
                    print('Connected by', add)
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        else:
                            aperture = int(data)
                            pump.launch(aperture)

    except SystemExit:
        print("Exit")
        pump.close()

if __name__ == "__main__":

    main()