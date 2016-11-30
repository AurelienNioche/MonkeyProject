import numpy as np


class StimuliFinder(object):
    def __init__(self):
        self.possible_p = [0.2, 5, 0.5, 0.75, 1]
        self.positive_x = np.arange(1, 5)
        self.negative_x = np.arange(-4, 1)

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

        self.conditions = \
            [
                self.p_fixed_x0_change_possible_loss_x1_fixed_zero,
                self.p_fixed_x0_change_positive_x1_fixed_possible_loss,
                self.p_change_x0_fixed_positive_x1_fixed_possible_loss,
                self.p_change_x0_fixed_possible_loss_x1_fixed_zero,
                self.safe_vs_possible_loss,
                self.random
            ]

    def find(self):
        np.random.choice(self.conditions, p=[0.1, 0.1, 0.1, 0.1, 0.3, 0.3])()

        return self.stimuli_parameters

    def p_fixed_x0_change_possible_loss_x1_fixed_zero(self):
        print("p: fixed; x0: possible loss; x1: equal to zero")

        single_p = np.random.choice(self.possible_p)
        x0 = np.random.choice(list(self.positive_x) + list(self.negative_x), size=2, replace=False)

        self.assign_values(p=[single_p, single_p], x0=x0, x1=[0, 0])

    def p_fixed_x0_change_positive_x1_fixed_possible_loss(self):
        print("p: fixed; x0: possible loss; x1: equal to zero")

        single_p = np.random.choice(self.possible_p)
        x0 = np.random.choice(self.positive_x, size=2, replace=False)
        single_x1 = np.random.choice(list(self.negative_x) + [0])

        self.assign_values(p=[single_p, single_p], x0=x0, x1=[single_x1, single_x1])

    def p_change_x0_fixed_positive_x1_fixed_possible_loss(self):
        print("p: change; x0: fixed and positive; x1: fixed and possible loss")

        p = np.random.choice(self.possible_p, size=2, replace=False)
        single_x0 = np.random.choice(self.positive_x)
        single_x1 = np.random.choice(list(self.positive_x) + list(self.negative_x))

        self.assign_values(p=p, x0=[single_x0, single_x0], x1=[single_x1, single_x1])

    def p_change_x0_fixed_possible_loss_x1_fixed_zero(self):
        print("p: change; x0: fixed and possible loss; x1: fixed and equal to zero")

        p = np.random.choice(self.possible_p, size=2, replace=False)
        single_x0 = np.random.choice(list(self.positive_x) + list(self.negative_x))

        self.assign_values(p=p, x0=[single_x0, single_x0], x1=[0, 0])

    def safe_vs_possible_loss(self):
        print("safe versus possible loss")

        p = sorted(np.random.choice(self.possible_p, size=2, replace=False), reverse=True)
        x0 = sorted(np.random.choice(self.positive_x, size=2, replace=False))
        x1 = [0, np.random.choice(self.negative_x)]

        self.assign_values(p=p, x0=x0, x1=x1)

    def random(self):
        print("random")

        p = np.random.choice(self.possible_p, size=2, replace=False)
        x0 = np.random.choice(self.positive_x, size=2, replace=False)
        x1 = np.random.choice(list(self.negative_x) + [0], size=2, replace=False)

        self.assign_values(p=p, x0=x0, x1=x1)

    def assign_values(self, p, x0, x1):
        idx = np.random.permutation(2)
        for i, side in zip(idx, self.sides):
            self.stimuli_parameters["{}_p".format(side)] = p[i]
            self.stimuli_parameters["{}_x0".format(side)] = x0[i]
            self.stimuli_parameters["{}_x1".format(side)] = x1[i]
            self.stimuli_parameters["{}_beginning_angle".format(side)] = np.random.randint(0, 360)


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


if __name__ == "__main__":
    main()