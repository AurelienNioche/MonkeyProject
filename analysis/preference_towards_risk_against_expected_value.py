from pylab import np, plt
from scipy.optimize import curve_fit
from os import makedirs

from data_management.data_manager import import_data
from utils.utils import log
from analysis.parameters import parameters
from analysis.tools.backup import Backup


""" 
Produce the figure which presents at which extent 
the risky option was chosen according to the difference between expected values
"""


def get_script_name():
    return __file__.split("/")[-1].split(".py")[0]


class Analyst(object):

    name = "Analyst 'Preference towards risk against expected value'"

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

    def get_choices_for_incongruent_trials(self, condition):

        results = {}

        n_trials = len(self.data["p"]["left"])

        for t in range(n_trials):

            if (not condition == "with_gains_only" or self.is_trial_with_gains_only(t)) and \
                    (not condition == "with_losses_only" or self.is_trial_with_losses_only(t)):

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

    def compute(self, results):

        expected_values_differences = []
        risky_choice_means = []
        n_trials = []

        r_keys = list(sorted(results.keys()))

        log("Pairs of lotteries used:", self.name)
        
        for i, alternative in enumerate(r_keys):

            delta = self.expected_value(alternative[0]) - self.expected_value(alternative[1])
            expected_values_differences.append(delta)

            mean = np.mean(results[alternative])
            risky_choice_means.append(mean)

            n = len(results[alternative])

            n_trials.append(n)

            log("({}) {} delta: {}, mean: {}, n: {}".format(i, alternative, delta, ", mean: ", mean, ", n:", n),
                self.name)

        log("Number of pairs of lotteries: {}".format(len(n_trials)), self.name)
        
        log("A few stats about the number of trials for a specific pair", self.name)
        
        log("Min: {}".format(np.min(n_trials)), self.name)
        log("Max: {}".format(np.max(n_trials)), self.name)
        log("Median {}:".format(np.median(n_trials)), self.name)
        log("Mean: {}".format(np.mean(n_trials)), self.name)
        log("Std: {}".format(np.std(n_trials)), self.name)
        log("Sum: {}".format(np.sum(n_trials)), self.name)
        
        return expected_values_differences, risky_choice_means, np.sum(n_trials)

    def run(self, condition):

        assert condition in ["with_gains_only", "with_losses_only"]

        log("Selected condition: {}".format(condition), self.name)

        results = self.get_choices_for_incongruent_trials(condition)

        expected_values_differences, risky_choice_means, n_trials = self.compute(results)

        log("N 'risky' trials  in condition '{}': {}".format(condition, n_trials), self.name)

        return expected_values_differences, risky_choice_means, n_trials


class RiskyChoiceAgainstExpectValuePlot(object):

    line_width = 3
    axis_label_font_size = 20
    ticks_label_font_size = 14
    legend_font_size = 14
    comment_font_size = 14
    point_size = 100

    name = "RiskyChoiceAgainstExpectValuePlot"

    def __init__(self):

        pass

    def plot(self, expected_values_differences, risky_choice_means, n_trials, color):

        x_data = expected_values_differences
        y_data = risky_choice_means

        try:

            p_opt, p_cov = curve_fit(self.sigmoid, x_data, y_data)

            n_points = 50  # Arbitrary neither too small, or too large
            x = np.linspace(min(x_data), max(x_data), n_points)
            y = self.sigmoid(x, *p_opt)
            plt.plot(x, y, color=color, label='fit', linewidth=self.line_width)

        except RuntimeError as e:
            log(e)

        plt.scatter(x_data, y_data, color=color, label='data', s=self.point_size)

        log("Plot results coming from {} trials".format(n_trials), self.name)

    def close_and_save(self, fig_name):

        plt.ylim(-0.01, 1.01)

        # Add comment for number of trials
        # plt.text(min(x_data) + 0.75 * (max(x_data) - min(x_data)), 0.1, "n trials: {}".format(n_trials),
        #          fontsize=self.comment_font_size)

        # Add legend
        # plt.legend(loc='upper left', fontsize=self.legend_font_size)

        # Axis labels
        plt.xlabel("$EV_{\mathrm{Riskiest\,Option}} - EV_{\mathrm{Safest\,Option}}$",
                   fontsize=self.axis_label_font_size)
        plt.ylabel("F(Choose riskiest option)",
                   fontsize=self.axis_label_font_size)

        # Remove top and right borders
        ax = plt.gca()
        ax.spines['right'].set_color('none')
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.spines['bottom'].set_position(('data', 0))
        ax.spines['top'].set_color('none')

        plt.tight_layout()

        plt.tick_params(axis='both', which='major', labelsize=self.ticks_label_font_size)
        plt.tick_params(axis='both', which='minor', labelsize=self.ticks_label_font_size)

        plt.savefig(fname=fig_name)
        plt.close()

    @staticmethod
    def sigmoid(x, x0, k):
        y = 1 / (1 + np.exp(-k * (x - x0)))
        return y


def main(force=False):

    makedirs(parameters.folders["figures"], exist_ok=True)

    for monkey in ["Havane", "Gladys"]:

        log(monkey, name="preference_towards_risk_against_expected_value.__main__")

        b = Backup(monkey, kind_of_analysis="data", folder=parameters.folders["pickle"])
        data = b.load()

        if force is True or data is None:

            starting_point = parameters.starting_points[monkey]
            data = import_data(monkey=monkey, starting_point=starting_point, end_point=parameters.end_point,
                               database_path=parameters.database_path)
            b.save(data)

        analyst = Analyst(data=data)

        plot = RiskyChoiceAgainstExpectValuePlot()

        results = {}

        for condition in ["with_gains_only", "with_losses_only"]:

            results[condition] = analyst.run(condition=condition)

            plot.plot(*results[condition], color="C0" if condition == "with_gains_only" else "C1")

            fig_name = "{}/{}_{}_{}.pdf" \
                .format(parameters.folders["figures"], monkey, get_script_name(), condition)

            plot.close_and_save(fig_name=fig_name)


if __name__ == "__main__":

    main()
