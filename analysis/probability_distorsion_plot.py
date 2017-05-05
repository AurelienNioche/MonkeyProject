from os import path
from pylab import np, plt
import json


class ProbabilityDistortionPlot(object):

    label_font_size = 12
    ticks_label_size = 8
    legend_font_size = 12

    line_width = 2

    n_points = 1000

    def __init__(self, parameters):

        self.parameters = parameters
        self.fig_name = self.get_fig_name()

    def get_fig_name(self):

        return path.expanduser("~/Desktop/probability_distortion_{:.2f}.pdf".format(
            self.parameters["probability_distortion"]))

    def w(self, p):
        """Probability distortion"""

        return np.exp(-(-np.log(p))**self.parameters["probability_distortion"])

    def plot(self):

        fig = plt.figure(figsize=(11.5, 7), dpi=300, facecolor='w')

        fig.subplots_adjust(left=0.15, right=0.9, bottom=0.2, top=0.9)

        ax = fig.add_subplot(1, 1, 1)

        X = np.linspace(0, 1, self.n_points)
        ax.plot(X, self.w(X), label=r'$\alpha = {}$'.format(self.parameters["probability_distortion"]),
                color="black", linewidth=self.line_width)

        ax.set_xlabel('$p$',
                      fontsize=self.label_font_size, labelpad=22)
        ax.set_ylabel('$w(p)$', fontsize=self.label_font_size, labelpad=12)

        ax.tick_params(labelsize=self.ticks_label_size)

        ax.set_ylim(0, 1)

        # ax.spines['left'].set_position(('data', 0))
        ax.spines['right'].set_color('none')
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        # ax.spines['bottom'].set_position(('data', 0))
        ax.spines['top'].set_color('none')

        # Add legend
        ax.legend(bbox_to_anchor=(0.2, 0.98), fontsize=self.legend_font_size, frameon=False)

        fig.savefig(self.fig_name)


def main():

    with open(path.expanduser("~/Desktop/results_monkey_modelling.json")) as f:
        data = json.load(f)

    for monkey in data.keys():
        pdp = ProbabilityDistortionPlot(parameters=data[monkey])
        pdp.plot()


if __name__ == "__main__":

    main()
