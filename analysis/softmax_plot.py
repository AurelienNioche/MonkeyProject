import os
from pylab import np, plt
import json

from analysis.parameters import parameters

"""
Produce result figure with softmax functions
"""


class SoftmaxPlot(object):

    label_font_size = 20
    ticks_label_size = 14
    # legend_font_size = 12

    line_width = 3

    def __init__(self, temp, monkey):

        self.temp = temp
        self.monkey = monkey
        self.fig_name = self.get_fig_name(monkey)

    def get_fig_name(self, monkey):

        os.makedirs(parameters.folders["figures"], exist_ok=True)

        return "{}/softmax_{}_temp_{:.2f}.pdf".format(parameters.folders["figures"], monkey, self.temp)

    def softmax(self, difference):

        """ Classic softmax function"""

        return 1/(1+np.exp(-difference/self.temp))

    def plot(self):

        # fig = plt.figure()
        # plt.subplots_adjust(left=0.15, right=0.9, bottom=0.2, top=0.9)

        x = np.arange(-1, 1, 0.01)
        plt.plot(
            x, self.softmax(x), label=r'$\tau = {}$'.format(self.temp),
            color="black", linewidth=self.line_width)

        plt.xlabel(
            '$U(L_1) - U(L_2)$\nMonkey {}.'.format(self.monkey[0]),
            fontsize=self.label_font_size, labelpad=22)
        plt.ylabel('P(Choose $L_1$)', fontsize=self.label_font_size, labelpad=12)

        plt.ylim(0, 1)
        plt.figaspect(1)

        ax = plt.gca()

        ax.spines['right'].set_color('none')
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.spines['top'].set_color('none')

        plt.xticks([-1, -0.5, 0, 0.5, 1], fontsize=self.ticks_label_size)
        plt.yticks([0, 0.25, 0.5, 0.75, 1], fontsize=self.ticks_label_size)

        # Add legend
        # ax.legend(bbox_to_anchor=(0.2, 0.98), fontsize=self.legend_font_size, frameon=False)

        plt.tight_layout()

        plt.savefig(self.fig_name)
        plt.close()


def main():

    for monkey in ["Havane", "Gladys"]:

        fit_results = "{}/{}_fit.json".format(parameters.folders["fit"], monkey)
        assert os.path.exists(fit_results), "I could not find the fit data.\n" \
                                            "Did you forgot to run the modeling script(analysis/modelling.py)?"

        # Open the file containing best parameters after fit
        with open(fit_results) as f:
            data = json.load(f)

        sp = SoftmaxPlot(temp=data["temp"], monkey=monkey)
        sp.plot()


if __name__ == "__main__":

    main()
