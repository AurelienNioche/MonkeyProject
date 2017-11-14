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

    def __init__(self, data):

        self.data = data

    @staticmethod
    def expected_value(lottery):
        return lottery[0] * lottery[1]

    def get_expected_values(self, t):

        return \
            self.data["p"]["left"][t] * \
            self.data["x0"]["left"][t], \
            self.data["p"]["right"][t] * \
            self.data["x0"]["right"][t]

    def is_trial_with_gains_only(self, t):

        return self.data["x0"]["left"][t] > 0 and self.data["x0"]["right"][t] > 0

    def is_trial_with_riskiest_option_on_left(self, t):

        return self.data["p"]["left"][t] < self.data["p"]["right"][t] and \
            np.absolute(self.data["x0"]["left"][t]) > np.absolute(self.data["x0"]["right"][t])

    def is_trial_with_riskiest_option_on_right(self, t):

        return self.data["p"]["left"][t] > self.data["p"]["right"][t] and \
            np.absolute(self.data["x0"]["left"][t]) < np.absolute(self.data["x0"]["right"][t])

    def get_sorted_data(self):

        results = {}

        n_trials = len(self.data["p"]["left"])

        for t in range(n_trials):

            if not self.is_trial_with_gains_only(t):

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

            if alternative not in results.keys():
                results[alternative] = []

            results[alternative].append(choose_risky)

        return results

    def analyse_by_pairs_of_lotteries(self, results):

        expected_values_differences = []
        risky_choice_means = []
        n_trials = 0

        r_keys = list(sorted(results.keys()))

        for i, alternative in enumerate(r_keys):

            delta = self.expected_value(alternative[0]) - self.expected_value(alternative[1])
            expected_values_differences.append(delta)

            mean = np.mean(results[alternative])
            risky_choice_means.append(mean)

            n = len(results[alternative])

            n_trials += n

            print(i, alternative, ", delta: ", delta, ", mean: ", mean, ", n:", n)

        # r = {}
        #
        # a = sorted(sorted_data["results"].keys())
        #
        # for i, l in enumerate(a):
        #
        #     m = np.mean(sorted_data["results"][l])
        #     # e = sem(sorted_data["results"][l])
        #
        #     n = len(sorted_data["results"][l])
        #
        #     ev = [l[i][0] * l[i][1] for i in range(2)]
        #
        #     mean_ev = np.mean(ev)
        #
        #     r[mean_ev] = {
        #         "m": m,
        #         "n": n,
        #         "delta": ev[0] - ev[1],
        #         "l": l
        #     }
        #
        # for i, key in enumerate(sorted(r.keys())):
        #     v = r[key]
        #     print(
        #         i, v["l"], "m = {m:.2f}, ev = {ev}, delta = {delta}, n = {n}".format(
        #             m=v["m"], ev=key, delta=v["delta"], n=v["n"]),
        #     )
        #
        # x = np.zeros(len(r))
        # y = np.zeros(len(r))
        # colors = np.zeros(len(r))
        #
        # for i, key in enumerate(sorted(r.keys())):
        #     v = r[key]
        #     x[i] = key
        #     y[i] = v["delta"]
        #     colors[i] = v["m"]
        #
        # area = 10 + np.pi * (15 * colors) ** 2  # 0 to 15 point radii
        #
        # plt.scatter(x, y, s=area, c=colors, alpha=0.5)
        #
        # file_name = folders["figures"] + monkey + "_" + get_script_name() + ".pdf"
        # plt.savefig(file_name)
        # plt.close()
        #
        # return r


def main(force=True):

    for monkey in ["Havane", "Gladys"]:

        print("\nAnalysis for {}...".format(monkey))

        starting_point = starting_points[monkey]

        # b = Backup(monkey, get_script_name())
        # sorted_data = b.load()

        # if force is True or sorted_data is None:

        data = import_data(monkey=monkey, starting_point=starting_point, end_point=end_point)
        analyst = Analyst(data=data)
        sorted_data = analyst.get_sorted_data()

        # b.save(sorted_data)

        results = analyst.analyse_by_pairs_of_lotteries(sorted_data)

        # log("N trials: {}".format(sorted_data["n_trials"]), "__main__")


if __name__ == "__main__":

    main()
