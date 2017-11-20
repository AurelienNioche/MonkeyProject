from pylab import np, plt
from scipy.stats import sem, wilcoxon, chisquare
from os import makedirs

from data_management.data_manager import import_data

from utils.utils import log

from analysis.backup import Backup

from analysis.analysis_parameters import folders, starting_points, end_point


def get_script_name():
    return __file__.split("/")[-1].split(".py")[0]


class Analyst:

    name = "Analyst"

    def __init__(self):

        self.data = None

    def equal_expected_value(self, t):

        return \
            self.data["p"]["left"][t] * \
            self.data["x0"]["left"][t] == \
            self.data["p"]["right"][t] * \
            self.data["x0"]["right"][t]

    def contains_a_certain_option(self, t):

        return self.data["p"]["left"][t] == 1. or self.data["p"]["right"][t] == 1.

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

    def get_sorted_data(self, data):

        self.data = data

        sorted_data = {"losses": {}, "gains": {}, "n_trials": 0}

        n_trials = len(self.data["p"]["left"])

        for t in range(n_trials):

            if not self.contains_a_certain_option(t):
                continue

            if not self.equal_expected_value(t):
                continue

            if self.is_trial_with_riskiest_option_on_left(t):

                risky, safe = "left", "right"

            elif self.is_trial_with_riskiest_option_on_right(t):

                risky, safe = "right", "left"

            else:
                continue

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

    def run(self, sorted_data):

        conditions = ("gains", "losses")

        # For plot
        results = {}

        # For Chi2
        import pandas as pd
        from scipy import stats

        data_frames = dict()

        for c in conditions:

            pairs = list(sorted_data[c].keys())
            log("For condition {}, I got {} pair(s) of lotteries ({}).".format(c, len(pairs), pairs), name=self.name)

            assert len(pairs) == 1, 'I expected only one pair of lotteries to meet the conditions.'

            chosen = sorted_data[c][pairs[0]]

            mean = np.mean(chosen)
            n = len(chosen)
            results[c] = mean

            print("Observed freq is {:.2f} ({} trials)".format(mean, n))

            # For Chi2
            n_hit = np.sum(chosen)

            data_frames[c] = pd.DataFrame(["yes"] * n_hit + ["no"] * (n - n_hit))
            data_frames[c] = pd.crosstab(index= data_frames[c][0], columns="count")

        print(data_frames)

        first_sample = data_frames["gains"]
        second_sample = data_frames["losses"]

        observed = first_sample
        expected = second_sample/len(second_sample) * len(first_sample)

        chi_squared_stat = (((observed - expected) ** 2) / expected).sum()

        print()
        print("Chi squared stat")
        print(chi_squared_stat)
        print()

        crit = stats.chi2.ppf(q=0.95,  # Find the critical value for 95% confidence*
                              df=1)  # Df = number of variable categories - 1

        print()
        print("Critical value")
        print(crit)

        p_value = 1 - stats.chi2.cdf(x=chi_squared_stat,  # Find the p-value
                                     df=1)

        print()
        print("P value")
        print(p_value)

        return results


class Plot(object):

    axis_label_font_size = 10

    def __init__(self, folder, monkey):

        self.fig_name = "{}/{}_equal_expected_value.pdf"\
            .format(folder, monkey)

    def plot(self, results):

        fig, ax = plt.subplots()

        names = ["Gain", "Loss"]

        ax.scatter(names, (results["gains"], results["losses"]), color=("C0", "C1"), s=80, zorder=2)

        ax.plot(names, (results["gains"], results["losses"]), color="black", zorder=1, alpha=0.5)
        ax.set_xlabel("\nLotteries potential outputs\n")

        ax.set_ylim(0, 1)
        plt.xticks(fontsize=8)

        ax.set_ylabel("Frequency with which the riskiest option is chosen",
                   fontsize=self.axis_label_font_size)

        ax.set_aspect(2)
        plt.tight_layout()
        # plt.legend()

        fig.savefig(fname=self.fig_name)
        plt.close()


def main(force=False):

    makedirs(folders["figures"], exist_ok=True)

    for monkey in ["Havane", "Gladys"]:

        print("\nAnalysis for {}...".format(monkey))

        starting_point = starting_points[monkey]

        analyst = Analyst()

        b = Backup(monkey, get_script_name())
        sorted_data = b.load()

        if force is True or sorted_data is None:

            data = import_data(monkey=monkey, starting_point=starting_point, end_point=end_point)
            sorted_data = analyst.get_sorted_data(data)

            b.save(sorted_data)

        n_trials = sorted_data["n_trials"]

        results = analyst.run(sorted_data)

        log("N trials: {}".format(n_trials), "__main__")

        plot = Plot(folder=folders["figures"], monkey=monkey)
        plot.plot(results)


if __name__ == "__main__":

    main()
