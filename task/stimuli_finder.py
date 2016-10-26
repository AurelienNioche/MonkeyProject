import numpy as np


class StimuliFinder(object):

    def __init__(self):

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

        # ------------------------------- #

        # # Uncomment for testing only probabilities
        #
        # self.possible_p = [0.25, 0.5, 0.75]
        # self.possible_q = [1, 2, 3, 4]
        #
        # self.find_stimuli = {"fixed_q": (self.find_stimuli_fixed_q, None)}

        # ------------------------------------- #

        # Comment for testing only probabilities
        self.possible_p = [0.25, 0.5, 0.75, 1]
        self.possible_q = [1, 2, 3, 4]

        self.expected_values = [-1.25, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1.25]

        # Associate a condition to a function to create stimuli parameters, with args

        self.find_stimuli = dict()
        self.find_stimuli["fixed_p"] = (self.find_stimuli_fixed_p, None)
        self.find_stimuli["fixed_q"] = (self.find_stimuli_fixed_q, None)
        self.find_stimuli["congruent"] = (self.find_stimuli_congruent, None)

        for i in self.expected_values:
            self.find_stimuli["incongruent_{}".format(i)] = (self.find_stimuli_incongruent, i)

        # ------------------------------- #

        self.possible_conditions = list(self.find_stimuli.keys())

        # ------------------------------- #

        self.sides = ["left", "right"]

        # ------------------------------- #

    def find(self):

        np.random.shuffle(self.sides)

        condition = np.random.choice(self.possible_conditions)

        # Call the good function according to the condition that has been selected
        f, arg = self.find_stimuli[condition]
        if arg is not None:
            f(arg)
        else:
            f()

        # Return stimuli parameters that have been created by function 'f'
        return self.stimuli_parameters

    def find_stimuli_fixed_p(self):

        print("FIXED P")

        p_left = np.random.choice(self.possible_p)
        x = np.random.choice(self.possible_q, size=2, replace=False)

        self.assign_values([p_left, p_left], x)

    def find_stimuli_fixed_q(self):

        print("FIXED Q")

        p = np.random.choice(self.possible_p, size=2, replace=False)
        x0 = np.random.choice(self.possible_q)

        self.assign_values(p, [x0, x0])

    def find_stimuli_congruent(self):

        print("CONGRUENT")

        p = np.sort(np.random.choice(self.possible_p, size=2, replace=False))
        x = np.sort(np.random.choice(self.possible_q, size=2, replace=False))

        self.assign_values(p, x)

    def find_stimuli_incongruent(self, expected_value):

        print("INCONGRUENT WITH DIFFERENCE IN EXPECTED VALUE OF {} IN (DE)FAVOR OF RISKY OPTION".format(expected_value))

        p = np.sort(np.random.choice(self.possible_p, size=2, replace=False))
        x = np.sort(np.random.choice(self.possible_q, size=2, replace=False))[::-1]

        while p[0]*x[0] - p[1]*x[1] != expected_value:

            p = np.sort(np.random.choice(self.possible_p, size=2, replace=False))
            x = np.sort(np.random.choice(self.possible_q, size=2, replace=False))[::-1]

        self.assign_values(p, x)

    def assign_values(self, p, x):

        for i, side in enumerate(self.sides):

            self.stimuli_parameters["{}_p".format(side)] = p[i]
            self.stimuli_parameters["{}_x0".format(side)] = x[i]
            self.stimuli_parameters["{}_x1".format(side)] = 0
            self.stimuli_parameters["{}_beginning_angle".format(side)] = np.random.randint(0, 360)


def main():

    # Only for purpose of testing
    stimuli_finder = StimuliFinder()
    result = stimuli_finder.find()
    print(result)


if __name__ == "__main__":

    main()