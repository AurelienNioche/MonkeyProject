from pylab import np, plt
from os import path
import json


class UtilityFunctionPlot(object):

    reward_max = 1
    reward_min = -1
    n_points = 1000
    axis_label_font_size = 15
    ticks_label_font_size = 8

    def __init__(self, parameters):

        self.parameters = parameters
        self.fig_name = self.get_fig_name()

    def get_fig_name(self):

        fig_name = path.expanduser("~/Desktop/utility_function")

        for key, value in sorted(self.parameters.items()):
            fig_name += "_{}_{:.2f}".format(key[:3], value)

        fig_name += ".pdf"
        return fig_name

    def u(self, x):

        """Compute utility for a single output considering a parameter of risk-aversion"""

        if x > 0:
            return (x/self.reward_max) ** (1-self.parameters["positive_risk_aversion"])
        else:
            return - ((np.absolute(x)/self.reward_max) ** self.parameters["negative_risk_aversion"]) \
                  / (1 - self.parameters["loss_aversion"])

    def plot(self):

        X = np.linspace(self.reward_min, self.reward_max, self.n_points)
        Y = [self.u(x) for x in X]

        ax = plt.gca()
        ax.plot(X, Y, color="black", linewidth=2)

        # plt.ylim(-0.05, 1.05)
        # plt.text(min(x_data) + 0.75 * (max(x_data) - min(x_data)), 0.1, "N trials: {}".format(n_trials))
        # plt.legend(loc='best')

        ax.spines['left'].set_position(('data', 0))
        ax.spines['right'].set_color('none')
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.spines['bottom'].set_position(('data', 0))
        ax.spines['top'].set_color('none')

        ax.set_xlabel("$x$", rotation=0, position=(0.9, None), fontsize=self.axis_label_font_size)
        ax.set_ylabel("$u(x)$", rotation=0, position=(None, 0.9), fontsize=self.axis_label_font_size)

        plt.tick_params(axis='both', which='major', labelsize=self.ticks_label_font_size)
        plt.tick_params(axis='both', which='minor', labelsize=self.ticks_label_font_size)

        plt.savefig(filename=self.fig_name)
        plt.close()


def main():

    with open(path.expanduser("~/Desktop/results_monkey_modelling.json")) as f:
        data = json.load(f)

    for monkey in ["Gladys", "Havane"]:
        ufp = UtilityFunctionPlot(parameters=data[monkey])
        ufp.plot()

if __name__ == "__main__":

    main()
