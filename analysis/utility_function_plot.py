from pylab import np, plt
from os import path, mkdir
import json

from analysis.modelling import ProspectTheoryModel
from analysis.analysis_parameters import folders


class UtilityFunctionPlot(object):

    reward_max = 3
    reward_min = -3
    n_points = 1000
    axis_label_font_size = 15
    ticks_label_font_size = 8

    def __init__(self, parameters, monkey):

        self.model = ProspectTheoryModel(
            parameters=[parameters[k] for k in ProspectTheoryModel.labels])
        self.fig_name = self.get_fig_name(monkey, parameters)

    @staticmethod
    def get_fig_name(monkey, parameters):

        if not path.exists(folders["figures"]):
            mkdir(folders["figures"])

        fig_name = "{}/utility_function_".format(folders["figures"])

        for key, value in sorted(parameters.items()):
            fig_name += "{}_{}_{:.2f}".format(monkey, key[:3], value)

        fig_name += ".pdf"
        return fig_name

    def plot(self):

        X = np.linspace(self.reward_min, self.reward_max, self.n_points)
        Y = [self.model.u(x) for x in X]

        X[:] = np.divide(X, self.reward_max)

        ax = plt.gca()
        ax.plot(X, Y, color="black", linewidth=2)

        ax.spines['left'].set_position(('data', 0))
        ax.spines['right'].set_color('none')
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.spines['bottom'].set_position(('data', 0))
        ax.spines['top'].set_color('none')

        ax.set_ylim([-1, 1])

        ax.set_xlabel("$x$", rotation=0, position=(0.9, None), fontsize=self.axis_label_font_size)
        ax.set_ylabel("$u(x)$", rotation=0, position=(None, 0.9), fontsize=self.axis_label_font_size)

        plt.tick_params(axis='both', which='major', labelsize=self.ticks_label_font_size)
        plt.tick_params(axis='both', which='minor', labelsize=self.ticks_label_font_size)

        plt.savefig(filename=self.fig_name)
        plt.close()


def main():

    for monkey in ["Gladys", "Havane"]:
        with open("{}/{}_result.json".format(folders["results"], monkey)) as f:
            data = json.load(f)

        ufp = UtilityFunctionPlot(monkey=monkey, parameters=data)
        ufp.plot()

if __name__ == "__main__":

    main()
