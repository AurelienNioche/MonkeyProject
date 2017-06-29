from pylab import np, plt
from scipy.optimize import curve_fit
from os import path, mkdir
import math

from data_management.data_manager import import_data
from utils.utils import log
from analysis.analysis_parameters import folders, starting_point, end_point


class Plot(object):

    axis_label_font_size = 12

    def __init__(self, fig_name):

        self.fig_name = fig_name

    def plot(self, results, monkey):

        fig, ax = plt.subplots()

        n_trials = results["n_trials"]

        bar_width = 0.25
        plt.bar([0], results["gains"]["average"], bar_width, yerr=results["gains"]["std"], label="gains")
        plt.bar([bar_width], results["losses"]["average"], bar_width, yerr=results["losses"]["std"], label="losses")

        ax.annotate('{} [n trials: {}]'.format(monkey, n_trials),
                    xy=(0, 0), xycoords='axes fraction', xytext=(0, 1.1))

        ax.set_ylim(0, 1)
        plt.tick_params(
            axis='x',  # changes apply to the x-axis
            which='both',  # both major and minor ticks are affected
            bottom='off',  # ticks along the bottom edge are off
            top='off',  # ticks along the top edge are off
            labelbottom='off')  # labels along the bottom edge are off

        # # Axis labels
        # plt.xlabel("Expected value of the two lotteries",
        #            fontsize=self.axis_label_font_size)
        plt.ylabel("Frequency with which the riskiest option is chosen",
                   fontsize=self.axis_label_font_size)

        ax.set_aspect(2)

        plt.legend()

        plt.savefig(filename=self.fig_name)
        plt.close()


class Analyst(object):

    name = "Analyst"

    def __init__(self, data):

        self.data = data

    def equal_expected_value(self, t):

        return \
            self.data["p"]["left"][t] * \
            self.data["x0"]["left"][t] == \
            self.data["p"]["right"][t] * \
            self.data["x0"]["right"][t]

    def is_trial_with_losses_only(self, t):

        return self.data["x0"]["left"][t] < 0 and self.data["x0"]["right"][t] < 0

    def is_trial_with_gains_only(self, t):

        return self.data["x0"]["left"][t] > 0 and self.data["x0"]["right"][t] > 0

    def is_trial_with_riskiest_option_on_left(self, t):

        if self.is_trial_with_gains_only(t) or self.is_trial_with_losses_only(t):

            return self.data["p"]["left"][t] < self.data["p"]["right"][t] and \
                np.absolute(self.data["x0"]["left"][t]) > np.absolute(self.data["x0"]["right"][t])

        else:
            return False

    def is_trial_with_riskiest_option_on_right(self, t):

        if self.is_trial_with_gains_only(t) or self.is_trial_with_losses_only(t):

            return self.data["p"]["left"][t] > self.data["p"]["right"][t] and \
                   np.absolute(self.data["x0"]["left"][t]) < np.absolute(self.data["x0"]["right"][t])

        else:
            return False

    def get_sorted_data(self):

        sorted_data = {"losses": {}, "gains": {}, "n_trials": 0}

        n_trials = len(self.data["p"]["left"])

        for t in range(n_trials):

            if self.equal_expected_value(t):

                if self.is_trial_with_riskiest_option_on_left(t):

                    risky, safe = "left", "right"

                elif self.is_trial_with_riskiest_option_on_right(t):

                    risky, safe = "right", "left"

                if "risky" in locals():

                    alternative = (
                        (self.data["p"][risky][t], self.data["x0"][risky][t]),
                        (self.data["p"][safe][t], self.data["x0"][safe][t])
                    )

                    choose_risky = int(self.data["choice"][t] == risky)

                    if self.is_trial_with_gains_only(t):
                        cond = "gains"

                    elif self.is_trial_with_losses_only(t):
                        cond = "losses"

                    else:
                        continue

                    if alternative not in sorted_data[cond].keys():
                        sorted_data[cond][alternative] = []

                    sorted_data[cond][alternative].append(choose_risky)

                    sorted_data["n_trials"] += 1

        return sorted_data

    @staticmethod
    def compute(sorted_data):

        results = {}

        for cond in ["gains", "losses"]:

            freq, n = [], []
            for value in sorted_data[cond].values():

                freq.append(np.mean(value))
                n.append(len(value))

            average = np.average(freq, weights=n)
            variance = np.average((np.asarray(freq) - average) ** 2, weights=n)
            std = math.sqrt(variance)

            results[cond] = {
                "average": average,
                "std": std
            }
        results["n_trials"] = sorted_data["n_trials"]
        return results

    def run(self):

        sorted_data = self.get_sorted_data()
        return self.compute(sorted_data)


def main():

    if not path.exists(folders["figures"]):
        mkdir(folders["figures"])

    for monkey in ["Havane", "Gladys"]:

        data = import_data(monkey=monkey, starting_point=starting_point, end_point=end_point)

        analyst = Analyst(data=data)
        results = analyst.run()

        log("N trials: {}".format(results["n_trials"]), "__main__")

        fig_name = "{}/{}_equal_expected_value.pdf"\
            .format(folders["figures"], monkey)

        plot = Plot(fig_name=fig_name)
        plot.plot(results, monkey)


if __name__ == "__main__":

    main()
