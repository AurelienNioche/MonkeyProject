from pylab import np, plt
from scipy.stats import sem, wilcoxon, chisquare
from os import makedirs

from data_management.data_manager import import_data

from utils.utils import log

from analysis.backup import Backup

from analysis.analysis_parameters import folders, starting_points, end_point


class Analyst:

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

    @staticmethod
    def analyse_pooled_four_categories(sorted_data):

        cond = ("gains", "losses")

        results = {}

        for c in cond:

            values = []

            for value in sorted_data[c].values():
                values += value

            # freq, n = [], []
            # for value in sorted_data[cond].values():
            #
            #     freq.append(np.mean(value))
            #     n.append(len(value))

            # average = np.average(freq, weights=n)
            # variance = np.average((np.asarray(freq) - average) ** 2, weights=n)
            # std = math.sqrt(variance)

            results[c] = {
                "mean": np.mean(values),
                "sem": sem(values)
            }
        results["n_trials"] = sorted_data["n_trials"]
        return results

    @staticmethod
    def analyse_by_pairs_of_lotteries(sorted_data):

        r = {}

        cond = ("gains", "losses")
        print()
        for c in cond:
            print("For {}:".format(c))
            a = sorted(sorted_data[c].keys())
            for i, l in enumerate(a):
                m = np.mean(sorted_data[c][l])
                e = sem(sorted_data[c][l])

                n = len(sorted_data[c][l])

                ev = l[0][0] * l[0][1]

                r[ev] = {
                    "m": m,
                    "n": n,
                    "e": e,
                    "l": l
                }
                print(
                    i, l, "m = {:.2f} [{:.2f}], ev = {}, n = {}".format(m, e, ev, n),
                )
            print()
        print()

        #
        # print(wilcoxon(r["gains"], r["losses"]))
        # print(chisquare(r["gains"]))
        # print(chisquare(r["losses"]))
        # print()

        return r


class Plot(object):

    axis_label_font_size = 10

    def __init__(self, folder, monkey):

        self.fig_name = "{}/{}_equal_expected_value.pdf"\
            .format(folder, monkey)

    def plot(self, results, monkey):

        fig, ax = plt.subplots()

        n_trials = results["n_trials"]

        bar_width = 0.25
        plt.bar([0], results["gains"]["mean"], bar_width, yerr=results["gains"]["sem"], label="gains")
        plt.bar([bar_width], results["losses"]["mean"], bar_width, yerr=results["losses"]["sem"], label="losses")

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


class PlotByPairs(object):

    axis_label_font_size = 10

    def __init__(self, folder, monkey):

        self.fig_name = "{}/{}_equal_expected_value_by_pairs.pdf"\
            .format(folder, monkey)

    def plot(self, results, monkey):

        evs = sorted(np.unique(np.absolute([i for i in results.keys()])))

        labels = ["{}\n\n{}\nvs\n{}\n".format(i, results[i]["l"][0], results[i]["l"][1]) for i in evs]

        n = len(evs)

        means1 = [results[i]["m"] for i in evs]
        means2 = [results[-i]["m"] for i in evs]

        sem1 = [results[i]["e"] for i in evs]
        sem2 = [results[-i]["e"] for i in evs]

        fig, ax = plt.subplots()

        ind = np.arange(n)  # the x locations for the groups
        width = 0.35  # the width of the bars

        rct_1 = ax.bar(ind, means1, width, color='C0', yerr=sem1)
        rct_2 = ax.bar(ind + width, means2, width, color='C1', yerr=sem2)

        ax.set_ylabel('Success rate')
        ax.set_ylim([0, 1])
        ax.set_title(monkey)

        ax.set_xticks(np.arange(n) + width / 2)
        ax.set_xticklabels(labels=labels)

        ax.legend((rct_1[0], rct_2[0]), ('Positive amounts', 'Negative amounts'))

        # ax.annotate('{} [n trials: {}]'.format(monkey, n_trials),
        #             xy=(0, 0), xycoords='axes fraction', xytext=(0, 1.1))

        ax.set_ylim(0, 1)

        # # Axis labels
        plt.xlabel("(Absolute) Expected value of the two lotteries",
                   fontsize=self.axis_label_font_size)
        plt.ylabel("Frequency with which the riskiest option is chosen",
                   fontsize=self.axis_label_font_size)

        ax.set_aspect(1.5)

        plt.savefig(filename=self.fig_name)
        plt.close()


def main(make_only_figures=True):

    makedirs(folders["figures"], exist_ok=True)

    for monkey in ["Havane", "Gladys"]:

        print("\nAnalysis for {}...".format(monkey))

        starting_point = starting_points[monkey]

        b = Backup(monkey, "equalExpectedValue")
        sorted_data = b.load()

        if not make_only_figures or sorted_data is None:

            data = import_data(monkey=monkey, starting_point=starting_point, end_point=end_point)
            analyst = Analyst(data=data)
            sorted_data = analyst.get_sorted_data()

            b.save(sorted_data)

        results1 = Analyst.analyse_pooled_four_categories(sorted_data)
        results2 = Analyst.analyse_by_pairs_of_lotteries(sorted_data)

        log("N trials: {}".format(sorted_data["n_trials"]), "__main__")

        plot = Plot(folder=folders["figures"], monkey=monkey)
        plot.plot(results1, monkey)

        plot = PlotByPairs(folder=folders["figures"], monkey=monkey)
        plot.plot(results2, monkey)


if __name__ == "__main__":

    main()
