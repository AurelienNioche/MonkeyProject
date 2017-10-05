import numpy as np


class ProspectTheoryModel(object):

    labels = ['loss_aversion', 'negative_risk_aversion', 'positive_risk_aversion', 'probability_distortion', 'temp']

    absolute_reward_max = 3

    def __init__(self, parameters):

        self.parameters = dict()

        for i, j in zip(sorted(self.labels), parameters):
            self.parameters[i] = j

        # self.norm = self.absolute_reward_max / (1 - self.parameters["loss_aversion"])

    def softmax(self, x1, x2):
        """Compute softmax values for each sets of scores in x."""
        # print("x", x)
        # return np.exp(x / tau) / np.sum(np.exp(x / tau), axis=0)
        return 1/(1+np.exp(-(1/self.parameters["temp"])*(x1-x2)))

    def u(self, x):
        """Compute utility for a single output considering a parameter of risk-aversion"""

        if x > 0:
            v = (x/self.absolute_reward_max) ** (1 - self.parameters["positive_risk_aversion"])

            if self.parameters["loss_aversion"] > 0:
                v = (1 - self.parameters["loss_aversion"]) * v

            assert 0. <= v <= 1.

        else:
            v = - (abs(x)/self.absolute_reward_max) ** (1 + self.parameters["negative_risk_aversion"])

            if self.parameters["loss_aversion"] < 0:
                v = (1 + self.parameters["loss_aversion"]) * v

            assert 0. >= v >= -1.

        return v

    def U(self, L):
        """Compute utility for a lottery"""

        p, v = L[0], L[1]
        y = self.w(p) * self.u(v)

        return y

    def w(self, p):
        """Probability distortion"""

        assert p > 0

        return np.exp(-(-np.log(p))**self.parameters["probability_distortion"])

    def get_p(self, lottery_0, lottery_1):

        """ Compute the probability of choosing lottery '0' against lottery '1' """

        # print(lottery_0, lottery_1)
        U0, U1 = self.U(lottery_0), self.U(lottery_1)

        p_choose_U0 = self.softmax(U0, U1)

        return p_choose_U0