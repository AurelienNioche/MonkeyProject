from pylab import np

from data_management.data_manager import import_data

from analysis.parameters import parameters
from analysis.tools.backup import Backup


"""
Compute the number of different pairs of lotteries
"""


def get_script_name():
    return __file__.split("/")[-1].split(".py")[0]


class Analyst(object):

    name = "Analyst"

    def __init__(self, data):

        self.data = data

    @staticmethod
    def expected_value(lottery):

        return lottery[0] * lottery[1]

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

    def is_trial_with_fixed_p(self, t):

        return self.data["p"]["left"][t] == self.data["p"]["right"][t]

    def is_trial_with_fixed_x(self, t):

        return self.data["x0"]["left"][t] == self.data["x0"]["right"][t]

    def is_trial_congruent(self, t):

        return (np.absolute(self.data["x0"]["left"][t]) > np.absolute(self.data["x0"]["right"][t]) and
                self.data["p"]["left"][t] > self.data["p"]["right"][t]) or \
               (np.absolute(self.data["x0"]["left"][t]) < np.absolute(self.data["x0"]["right"][t]) and
                self.data["p"]["left"][t] < self.data["p"]["right"][t])

    def which_type_of_control(self, t):

        type_of_control = False

        if self.is_trial_with_fixed_p(t):

            if self.is_trial_with_gains_only(t):
                type_of_control = "identical p, positive x0"

            elif self.is_trial_with_losses_only(t):
                type_of_control = "identical p, negative x0"

            else:
                type_of_control = "identical p, positive vs negative x0"

        elif self.is_trial_with_fixed_x(t):

            if self.is_trial_with_gains_only(t):
                type_of_control = "identical x, positive x0"

            elif self.is_trial_with_losses_only(t):
                type_of_control = "identical x, negative x0"

            else:
                raise Exception("Revise your logic!")

        elif self.is_trial_congruent(t):
            type_of_control = "congruent"

        return type_of_control

    def is_trial_with_best_option_on_left(self, t):

        condition = self.which_type_of_control(t)
        # print("...is a control trial ({})".format(condition))

        if condition in \
                ("identical p, positive vs negative x0",
                 "identical p, negative x0",
                 "identical p, positive x0",
                 "congruent"):
            return self.data["x0"]["left"][t] > self.data["x0"]["right"][t]

        elif condition == "identical x, negative x0":
            return self.data["p"]["left"][t] < self.data["p"]["right"][t]

        elif condition == "identical x, positive x0":
            return self.data["p"]["left"][t] > self.data["p"]["right"][t]

        else:
            return False

    def is_trial_with_best_option_on_right(self, t):

        condition = self.which_type_of_control(t)

        if condition in \
                ("identical p, positive vs negative x0",
                 "identical p, negative x0",
                 "identical p, positive x0",
                 "congruent"):
            return not self.data["x0"]["left"][t] > self.data["x0"]["right"][t]

        elif condition == "identical x, negative x0":
            return not self.data["p"]["left"][t] < self.data["p"]["right"][t]

        elif condition == "identical x, positive x0":
            return not self.data["p"]["left"][t] > self.data["p"]["right"][t]

        else:
            return False

    def is_trial_identical_pairs(self, t):

        return self.data["x0"]["left"][t] == self.data["x0"]["right"][t] and \
                self.data["p"]["left"][t] == self.data["p"]["right"][t]

    def get_choices(self):

        results = {}

        n_trials = len(self.data["p"]["left"])

        for t in range(n_trials):

            # print("Pair of lottery:", self.data["p"]["left"][t],
            # self.data["x0"]["left"][t], self.data["p"]["right"][t],
            #       self.data["x0"]["right"][t])

            if self.is_trial_identical_pairs(t):
                raise Exception("It should not be the case")

            elif self.is_trial_with_riskiest_option_on_left(t):
                first, second = "left", "right"
                # print("... is a trial with riskiest option on the left.")

            elif self.is_trial_with_best_option_on_left(t):
                first, second = "left", "right"
                # print("... is a trial with best option on the left.")

            elif self.is_trial_with_riskiest_option_on_right(t):
                first, second = "right", "left"
                # print("... is a trial with riskiest option on the right.")

            elif self.is_trial_with_best_option_on_right(t):
                first, second = "right", "left"
                # print("... is a trial with best option on the right.")

            else:
                raise Exception

            alternative = (
                (self.data["p"][first][t], self.data["x0"][first][t]),
                (self.data["p"][second][t], self.data["x0"][second][t])
            )

            choose_first = int(self.data["choice"][t] == first)

            if alternative not in results.keys():
                results[alternative] = []

            results[alternative].append(choose_first)

        return results

    def compute(self, results):

        import itertools as it

        p = (0.25, 0.5, 0.75, 1)
        x = (-3, -2, -1, 1, 2, 3)
        st = [i for i in it.product(p, x)]

        all_alt = [i for i in it.combinations(st, r=2)]

        print(len(all_alt))

        r_keys = list(sorted(results.keys()))
        for i, alt in enumerate(r_keys):
            if alt not in all_alt and (alt[::-1]) not in all_alt:
                print(alt)
                raise Exception

        print("Among the {} combinations possible, the following lottery pairs have been excluded:".format(len(all_alt)))
        for i, alt in enumerate(all_alt):

            if alt not in r_keys and (alt[::-1]) not in r_keys:
                print(alt)

        expected_values_differences = []
        means = []
        n_trials = []

        r_keys = list(sorted(results.keys()))

        print()
        print("Pairs of lotteries used:")
        print()
        for i, alternative in enumerate(r_keys):

            delta = self.expected_value(alternative[0]) - self.expected_value(alternative[1])
            expected_values_differences.append(delta)

            mean = np.mean(results[alternative])
            means.append(mean)

            n = len(results[alternative])

            n_trials.append(n)

            print(i, alternative, ", delta: ", delta, ", mean: ", mean, ", n:", n)

        print()
        print("Number of pairs of lotteries", len(n_trials))

        print()
        print("Analysis of the number of trials")
        print()

        print("Min:", np.min(n_trials))
        print("Max:", np.max(n_trials))
        print("Median:", np.median(n_trials))
        print("Mean:", np.mean(n_trials))
        print("Std:", np.std(n_trials))
        print("Sum:", np.sum(n_trials))

        print()
        return expected_values_differences, means, np.sum(n_trials)

    def run(self):

        results = self.get_choices()

        expected_values_differences, risky_choice_means, n_trials = self.compute(results)

        return expected_values_differences, risky_choice_means, n_trials


def main(force=False):

    for monkey in ["Havane", "Gladys"]:

        print()
        print(monkey.upper())
        print()

        b = Backup(monkey, kind_of_analysis="data", folder=parameters.folders["pickle"])
        data = b.load()

        if force is True or data is None:

            starting_point = parameters.starting_points[monkey]
            data = import_data(monkey=monkey, starting_point=starting_point, end_point=parameters.end_point)
            b.save(data)

        analyst = Analyst(data=data)

        analyst.run()


if __name__ == "__main__":

    main()
