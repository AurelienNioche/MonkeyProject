from pylab import np, plt
import os
import json

from analysis.modelling import ProspectTheoryModel
from analysis.parameters import parameters


"""
Produce the utility function figure
"""


class UtilityFunctionPlot(object):

    reward_max = 3
    reward_min = -3
    n_points = 1000
    axis_label_font_size = 20
    ticks_label_font_size = 14
    line_width = 3

    def __init__(self, param, monkey):

        self.model = ProspectTheoryModel(
            parameters=[param[k] for k in ProspectTheoryModel.labels])
        self.fig_name = self.get_fig_name(monkey, param)

    @staticmethod
    def get_fig_name(monkey, param):

        os.makedirs(parameters.folders["figures"], exist_ok=True)

        fig_name = "{}/utility_function_{}_".format(parameters.folders["figures"], monkey)

        for key, value in sorted(param.items()):
            fig_name += "{}_{:.2f}".format(key[:3], value)

        fig_name += ".pdf"
        return fig_name

    def plot(self):

        x = np.linspace(self.reward_min, self.reward_max, self.n_points)
        y = [self.model.u(i) for i in x]

        x[:] = np.divide(x, self.reward_max)

        ax = plt.gca()
        ax.plot(x, y, color="black", linewidth=self.line_width)

        ax.spines['left'].set_position(('data', 0))
        ax.spines['right'].set_color('none')
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.spines['bottom'].set_position(('data', 0))
        ax.spines['top'].set_color('none')

        ax.set_ylim([-1, 1])
        ax.set_xlim([-1, 1])

        ax.set_xlabel("$x$", rotation=0, position=(0.9, None), fontsize=self.axis_label_font_size)
        ax.set_ylabel("$u(x)$", rotation=0, position=(None, 0.9), fontsize=self.axis_label_font_size)

        plt.tick_params(axis='both', which='major', labelsize=self.ticks_label_font_size)
        plt.tick_params(axis='both', which='minor', labelsize=self.ticks_label_font_size)

        plt.xticks([-1, -0.5, 0.5, 1])
        plt.yticks([-1, -0.5, 0.5, 1])

        ax.set_aspect(1)

        plt.tight_layout()

        plt.savefig(fname=self.fig_name)
        plt.close()


def main():

    for monkey in ["Gladys", "Havane"]:

        fit_results = "{}/{}_fit.json".format(parameters.folders["fit"], monkey)
        assert os.path.exists(fit_results), "I could not find the fit data.\n" \
                                            "Did you forgot to run the modeling script(analysis/modelling.py)?"

        # Open the file containing best parameters after fit
        with open(fit_results) as f:
            data = json.load(f)

        ufp = UtilityFunctionPlot(monkey=monkey, param=data)
        ufp.plot()


if __name__ == "__main__":

    main()
