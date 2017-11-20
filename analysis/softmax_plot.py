from os import path, mkdir
from pylab import np, plt
import json

from analysis.analysis_parameters import folders


class SoftmaxPlot(object):

    label_font_size = 12
    ticks_label_size = 8
    legend_font_size = 12

    line_width = 2

    def __init__(self, temp, monkey):

        self.temp = temp
        self.fig_name = self.get_fig_name(monkey)

    def get_fig_name(self, monkey):

        if not path.exists(folders["figures"]):
            mkdir(folders["figures"])

        return "{}/softmax_{}_temp_{:.2f}.pdf".format(folders["figures"], monkey, self.temp)

    def softmax(self, difference):

        """ Classic softmax function"""

        return 1/(1+np.exp(-difference/self.temp))

    def plot(self):

        #fig = plt.figure()

        plt.subplots_adjust(left=0.15, right=0.9, bottom=0.2, top=0.9)

        #ax = fig.add_subplot(1, 1, 1)

        X = np.arange(-1, 1, 0.01)
        plt.plot(X, self.softmax(X), label=r'$\tau = {}$'.format(self.temp),
                color="black", linewidth=self.line_width)

        plt.xlabel('Difference between the (subjective) value of lottery $L1$ and $L2$',
                      fontsize=self.label_font_size, labelpad=22)
        plt.ylabel('Probability of choosing lottery $L1$', fontsize=self.label_font_size, labelpad=12)

        # ax.tick_params(labelsize=self.ticks_label_size)

        plt.ylim(0, 1)
        plt.figaspect(1)

        # ax.spines['left'].set_position(('data', 0))
        #ax.spines['right'].set_color('none')
        #ax.xaxis.set_ticks_position('bottom')
        #ax.yaxis.set_ticks_position('left')
        ## ax.spines['bottom'].set_position(('data', 0))
        #ax.spines['top'].set_color('none')

        #ax.set_aspect("equal")
        # Add legend
        # ax.legend(bbox_to_anchor=(0.2, 0.98), fontsize=self.legend_font_size, frameon=False)

        plt.savefig(self.fig_name)
        plt.close()


def main():

    for monkey in ["Havane", "Gladys"]:

        with open("{}/{}_result.json".format(folders["results"], monkey)) as f:
            data = json.load(f)

        sp = SoftmaxPlot(temp=data["temp"], monkey=monkey)
        sp.plot()


if __name__ == "__main__":

    main()
