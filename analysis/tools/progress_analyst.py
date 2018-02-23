import numpy as np

"""
module to sort the control trials and assess the behavioral performances
"""


class ProgressAnalyst(object):

    control_conditions = [
        "identical p, negative x0",
        "identical p, positive x0",
        "identical p, positive vs negative x0",
        "identical x, negative x0",
        "identical x, positive x0"
    ]

    def __init__(self, p, x0, choice):

        self.p = p
        self.x0 = x0

        self.choice = choice
        self.trials_id = np.arange(len(self.p["left"]))

        self.dict_functions = dict()
        for key in self.control_conditions:
            self.dict_functions[key] = getattr(self, 'analyse_{}'.format(key.replace(" ", "_").replace(",", "")))

    def analyse(self, condition):

        return self.dict_functions[condition]()

    def analyse_identical_p_negative_x0(self):

        n = 0
        hit = 0

        assert len(self.choice) == len(self.trials_id)

        for i in self.trials_id:

            if self.p["left"][i] == self.p["right"][i] \
                    and self.x0["left"][i] < 0 and self.x0["right"][i] < 0:

                n += 1

                if (self.choice[i] == "left") == (self.x0["left"][i] > self.x0["right"][i]):

                    hit += 1
        if n:

            print("Success rate with identical p, negative x0: {:.2f}".format(hit / n))
            return hit / n

    def analyse_identical_p_positive_x0(self):

        n = 0
        hit = 0

        assert len(self.choice) == len(self.trials_id)

        for i in self.trials_id:

            if self.p["left"][i] == self.p["right"][i] \
                    and self.x0["left"][i] > 0 and self.x0["right"][i] > 0:

                n += 1

                if (self.choice[i] == "left") == (self.x0["left"][i] > self.x0["right"][i]):

                    hit += 1
        if n:
            print("Success rate with identical p, positive x0: {:.2f}".format(hit / n))
            return hit / n

    def analyse_identical_p_positive_vs_negative_x0(self):

        n = 0
        hit = 0

        assert len(self.choice) == len(self.trials_id)

        for i in self.trials_id:

            if self.p["left"][i] == self.p["right"][i] \
                    and (self.x0["left"][i] > 0 > self.x0["right"][i] or
                         self.x0["left"][i] < 0 < self.x0["right"][i]):

                n += 1

                if (self.choice[i] == "left") == (self.x0["left"][i] > self.x0["right"][i]):

                    hit += 1

        if n:

            print("Success rate with identical p, positive vs negative x0: {:.2f}".format(hit / n))
            return hit / n

    def analyse_identical_x_positive_x0(self):

        n = 0
        hit = 0

        for i in self.trials_id:

            if self.x0["left"][i] == self.x0["right"][i] \
                    and self.x0["left"][i] > 0:

                n += 1

                if (self.choice[i] == "left") == (self.p["left"][i] > self.p["right"][i]):
                    hit += 1
        if n:
            print("Success rate with identical x, positive x0: {:.2f}".format(hit / n))
            return hit / n

    def analyse_identical_x_negative_x0(self):

        n = 0
        hit = 0

        for i in self.trials_id:

            if self.x0["left"][i] == self.x0["right"][i] \
                    and self.x0["left"][i] < 0:

                n += 1

                if (self.choice[i] == "left") == (self.p["left"][i] < self.p["right"][i]):
                    hit += 1

        if n:
            print("Success rate with identical x, negative x0: {:.2f}".format(hit / n))
            return hit / n
