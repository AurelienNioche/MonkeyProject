from pylab import np, plt
from scipy.optimize import curve_fit
from os import makedirs

from data_management.data_manager import import_data
from utils.utils import log
from analysis.analysis_parameters import folders, starting_points, end_point


class RiskyChoiceAgainstExpectValuePlot(object):

    line_width = 2
    axis_label_font_size = 8
    ticks_label_font_size = 8
    legend_font_size = 8
    comment_font_size = 8

    def __init__(self, fig_name):

        self.fig_name = fig_name

    def plot(self, expected_values_differences, risky_choice_means, n_trials):

        x_data = expected_values_differences
        y_data = risky_choice_means

        try:

            p_opt, p_cov = curve_fit(self.sigmoid, x_data, y_data)

            n_points = 50  # Arbitrary neither too small, or too large
            x = np.linspace(min(x_data), max(x_data), n_points)
            y = self.sigmoid(x, *p_opt)
            plt.plot(x, y, color="black", label='fit', linewidth=self.line_width)

        except RuntimeError as e:
            print(e)

        plt.plot(x_data, y_data, 'o', color="black", label='data')
        plt.ylim(-0.01, 1.01)

        # Add comment for number of trials
        plt.text(min(x_data) + 0.75 * (max(x_data) - min(x_data)), 0.1, "n trials: {}".format(n_trials),
                 fontsize=self.comment_font_size)

        # Add legend
        plt.legend(loc='best', fontsize=self.legend_font_size)

        # Axis labels
        plt.xlabel("Difference between the expected values of the riskiest option and the safest option",
                   fontsize=self.axis_label_font_size)
        plt.ylabel("Frequency with which the riskiest option is chosen",
                   fontsize=self.axis_label_font_size)

        # Remove top and right borders
        ax = plt.gca()
        ax.spines['right'].set_color('none')
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.spines['bottom'].set_position(('data', 0))
        ax.spines['top'].set_color('none')

        plt.tick_params(axis='both', which='major', labelsize=self.ticks_label_font_size)
        plt.tick_params(axis='both', which='minor', labelsize=self.ticks_label_font_size)

        plt.savefig(filename=self.fig_name)
        plt.close()

    @staticmethod
    def sigmoid(x, x0, k):
        y = 1 / (1 + np.exp(-k * (x - x0)))
        return y


class Analyst(object):

    name = "Analyst"

    def __init__(self, data, condition=""):

        self.data = data

        self.condition = condition
        assert self.condition in ["with_gains_only", "with_losses_only"]

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

    def get_choices_for_incongruent_trials(self):

        results = {}

        n_trials = len(self.data["p"]["left"])

        for t in range(n_trials):

            if (not self.condition == "with_gains_only" or self.is_trial_with_gains_only(t)) and \
                    (not self.condition == "with_losses_only" or self.is_trial_with_losses_only(t)):

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

        return expected_values_differences, risky_choice_means, n_trials

    def run(self):

        log("Selected condition: {}".format(self.condition), self.name)

        results = self.get_choices_for_incongruent_trials()

        expected_values_differences, risky_choice_means, n_trials = self.compute(results)

        log("N 'risky' trials with selected condition: {}".format(n_trials), self.name)

        return expected_values_differences, risky_choice_means, n_trials


def main():

    makedirs(folders["figures"], exist_ok=True)

    for monkey in ["Havane", "Gladys"]:

        starting_point = starting_points[monkey]

        data = import_data(monkey=monkey, starting_point=starting_point, end_point=end_point)

        for condition in ["with_gains_only", "with_losses_only"]:

            fig_name = "{}/{}_preference_toward_risk_against_EV_{}.pdf"\
                .format(folders["figures"], monkey, condition)

            analyst = Analyst(data=data, condition=condition)
            results = analyst.run()

            plot = RiskyChoiceAgainstExpectValuePlot(fig_name=fig_name)
            plot.plot(*results)


if __name__ == "__main__":

    main()
