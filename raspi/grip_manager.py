import socket
import RPi.GPIO as GPIO


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

    host = ''  # Symbolic name meaning all available interfaces
    port = 1556  # Arbitrary non-privileged port

    try:

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

            s.bind((host, port))
            s.listen(1)
            while True:

                print("Waiting for connection...")
                conn, addr = s.accept()
                detector_state = 0

                with conn:

                    print('Connected by', addr)
                    while True:

                        try:
                            new_detector_state = grip.detect()

                            if detector_state != new_detector_state:

                                conn.send("{}".format(new_detector_state).encode())
                                detector_state = new_detector_state

                        except socket.error as exc:
                            print("Caught exception socket.error: {}".format(exc))
                            break

    except (SystemExit, KeyboardInterrupt):

        print("Exit")
        grip.close()


if __name__ == "__main__":

    main()
