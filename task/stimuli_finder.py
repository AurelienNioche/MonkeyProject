import numpy as np
from threading import Thread
from multiprocessing import Queue
from PyQt5.QtWidgets import QApplication
from collections import OrderedDict
from task.game_window import GameWindow
import sys


class StimuliFinder(object):
    def __init__(self):

        self.gauge_maximum = 6
        self.maximum_x = 3

        self.possible_p = [0.25, 0.5, 0.75, 1]
        self.positive_x = np.arange(1, 4)
        self.negative_x = np.arange(-3, 0)

        self.stimuli_parameters = {
            "left_p": 0,
            "left_x0": 0,
            "left_x1": 0,
            "left_beginning_angle": 0,
            "right_p": 0,
            "right_x0": 0,
            "right_x1": 0,
            "right_beginning_angle": 0

        }

        self.sides = ["left", "right"]

        self.conditions = OrderedDict(
            [
                (self.p_fixed_x0_positive, 0.25),
                (self.p_fixed_x0_negative, 0.25),
                (self.p_fixed_x0_negative_vs_positive, 0.25),
                (self.x_fixed, 0.25),
                (self.congruent_negative, 0),
                (self.congruent_positive, 0),
                (self.incongruent_positive, 0),
                (self.incongruent_negative, 0)
            ]
        )

    def find(self):

        # p could be [i for i in self.conditions.values()]
        return np.random.choice([i for i in self.conditions.keys()], p=None)()

    def p_fixed_x0_positive(self):

        print("StimulusFinder: p fixed; x0 positive.")

        single_p = np.random.choice(self.possible_p)
        x0 = np.random.choice(self.positive_x, size=2, replace=False)

        return self.assign_values(p=[single_p, single_p], x0=x0, x1=[0, 0])

    def p_fixed_x0_negative(self):

        print("StimulusFinder: p fixed; x0 negative.")

        single_p = np.random.choice(self.possible_p)
        x0 = np.random.choice(self.negative_x, size=2, replace=False)

        return self.assign_values(p=[single_p, single_p], x0=x0, x1=[0, 0])

    def p_fixed_x0_negative_vs_positive(self):

        print("StimulusFinder: p fixed; x0 negative vs positive.")

        single_p = np.random.choice(self.possible_p)
        x0 = [np.random.choice(self.negative_x), np.random.choice(self.positive_x)]

        return self.assign_values(p=[single_p, single_p], x0=x0, x1=[0, 0])

    def x_fixed(self):

        print("StimulusFinder: x fixed.")

        p = np.random.choice(self.possible_p, size=2, replace=False)
        single_x0 = np.random.choice(list(self.positive_x) + list(self.negative_x))

        return self.assign_values(p=p, x0=[single_x0, single_x0], x1=[0, 0])

    def congruent_positive(self):

        print("StimulusFinder: congruent positive.")

        p = sorted(np.random.choice(self.possible_p, size=2, replace=False))
        x0 = sorted(np.random.choice(self.positive_x, size=2, replace=False))

        return self.assign_values(p=p, x0=x0, x1=[0, 0])

    def congruent_negative(self):

        print("StimulusFinder: congruent negative.")

        p = sorted(np.random.choice(self.possible_p, size=2, replace=False))
        x0 = sorted(np.random.choice(self.negative_x, size=2, replace=False))

        return self.assign_values(p=p, x0=x0, x1=[0, 0])

    def incongruent_positive(self):

        print("StimulusFinder: incongruent positive.")

        p = sorted(np.random.choice(self.possible_p, size=2, replace=False))
        x0 = sorted(np.random.choice(self.positive_x, size=2, replace=False), reverse=True)

        return self.assign_values(p=p, x0=x0, x1=[0, 0])

    def incongruent_negative(self):

        print("StimulusFinder: incongruent negative.")

        p = sorted(np.random.choice(self.possible_p, size=2, replace=False))
        x0 = sorted(np.random.choice(self.negative_x, size=2, replace=False), reverse=True)

        return self.assign_values(p=p, x0=x0, x1=[0, 0])

    def random(self):

        print("StimulusFinder: Random")
        while True:

            p = np.random.choice(self.possible_p, size=2)
            x0 = np.zeros(2, dtype=int)
            x1 = np.zeros(2, dtype=int)
            x0[0], x1[0] = np.random.choice(list(self.negative_x) + [0] + list(self.positive_x), size=2, replace=False)
            x0[1], x1[1] = np.random.choice(list(self.negative_x) + [0] + list(self.positive_x), size=2, replace=False)

            if p[0] == p[1]:

                if x0[0] == x0[1] and x1[0] == x1[1]:
                    pass

                else:
                    break

            elif p[0] == 1 - p[1]:

                if x0[0] == x1[1] and x1[0] == x0[0]:
                    pass

                else:
                    break

            else:
                break

        return self.assign_values(p=p, x0=x0, x1=x1)

    def assign_values(self, p, x0, x1):

        idx = np.random.permutation(2)
        for i, side in zip(idx, self.sides):
            self.stimuli_parameters["{}_p".format(side)] = p[i]
            self.stimuli_parameters["{}_x0".format(side)] = x0[i]
            self.stimuli_parameters["{}_x1".format(side)] = x1[i]
            self.stimuli_parameters["{}_beginning_angle".format(side)] = np.random.randint(0, 360)

        return self.stimuli_parameters

# ----------------------------------------------- #


def main():

    gain_expectation = []

    for i in range(10000):

        sf = StimuliFinder()
        sp = sf.find()
        gain_expectation.append(
            np.mean(
                [
                    sp["left_p"] * sp["left_x0"] + (1 - sp["left_p"]) * sp["left_x1"],
                    sp["right_p"] * sp["right_x0"] + (1 - sp["right_p"]) * sp["right_x1"]
                ]
            )
        )
    print("Gain expectation in average:", np.mean(gain_expectation))


# ----------------------------------------------- #

def test_stimuli(win):

    sf = StimuliFinder()
    sp = sf.find()

    win.current_step = "show_stimuli"
    win.set_parameters(sp)

    # Just tap 'enter' to generate a new stimuli
    while True:
        a = input()
        if a == "quit()":
            break
        else:
            sp = sf.find()
            win.set_parameters(sp)
            win.show_stimuli()


def main_visual():

    app = QApplication(sys.argv)

    window = GameWindow(queue=Queue(), textures_folder="../textures", standalone=True)
    window.show()

    pro = Thread(target=test_stimuli, args=(window,))
    pro.start()

    sys.exit(app.exec_())

# ----------------------------------------------- #


def test_difference_expected_value():

    sf = StimuliFinder()

    diff = []

    for i in range(10000):

        sp = sf.incongruent_positive()

        exp = {}
        for side in ["left", "right"]:
            exp[side] = \
                sp["{}_p".format(side)] * sp["{}_x0".format(side)] + \
                (1 - sp["{}_p".format(side)]) * sp["{}_x1".format(side)]
        diff.append(exp["left"] - exp["right"])

    print(np.unique(diff))


if __name__ == "__main__":

    main_visual()


