from os import path, mkdir
from pylab import np, plt
import json

from analysis.analysis_parameters import folders


class ProbabilityDistortionPlot:

    label_font_size = 20
    ticks_label_size = 14
    # legend_font_size = 12

    line_width = 3

    n_points = 1000

    def __init__(self, monkey, alpha):

        self.alpha = alpha
        self.monkey = monkey
        self.fig_name = self.get_fig_name(monkey)

    def get_fig_name(self, monkey):

        if not path.exists(folders["figures"]):
            mkdir(folders["figures"])

        return "{}/probability_distortion_{}_{:.2f}.pdf".format(
            folders["figures"], monkey, self.alpha)

    def w(self, p):
        """Probability distortion"""

        return np.exp(-(-np.log(p))**self.alpha)

    def plot(self):

        # fig = plt.figure(figsize=(11.5, 7), dpi=300, facecolor='w')

        #fig.subplots_adjust(left=0.15, right=0.9, bottom=0.2, top=0.9)
        plt.subplots_adjust(left=0.15, right=0.9, bottom=0.2, top=0.9)
        #ax = fig.add_subplot(1, 1, 1)

        X = np.linspace(0.001, 1, self.n_points)
        plt.plot(
            X, self.w(X), label=r'$\alpha = {}$'.format(self.alpha),
            color="black", linewidth=self.line_width)

        plt.xlabel('$p$\nMonkey {}.'.format(self.monkey[0]), fontsize=self.label_font_size)
        plt.ylabel('$w(p)$', fontsize=self.label_font_size)

        plt.ylim(0, 1)
        plt.figaspect(1)

        ax = plt.gca()

        ax.spines['right'].set_color('none')
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.spines['top'].set_color('none')

        plt.xticks([0, 0.25, 0.5, 0.75, 1], fontsize=self.ticks_label_size)
        plt.yticks([0, 0.25, 0.5, 0.75, 1], fontsize=self.ticks_label_size)

        # Add legend
        # ax.legend(bbox_to_anchor=(0.2, 0.98), fontsize=self.legend_font_size, frameon=False)

        plt.figaspect(1)

        plt.savefig(self.fig_name)

        plt.close()


def main():

    for monkey in ["Havane", "Gladys"]:

        with open("{}/{}_result.json".format(folders["fit"], monkey)) as f:
            data = json.load(f)

        pdp = ProbabilityDistortionPlot(monkey=monkey, alpha=data["probability_distortion"])
        pdp.plot()


if __name__ == "__main__":

    main()
