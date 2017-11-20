from pylab import np, plt
from os import makedirs

from data_management.data_manager import import_data

from analysis.analysis_parameters import folders, starting_points, end_point
from analysis.backup import Backup


# from utils.utils import log


def get_script_name():

    return __file__.split("/")[-1].split(".py")[0]


class Analyst(object):

    control_conditions = [
        "identical p, positive vs negative x0",
        "identical p, positive x0",
        "identical p, negative x0",
        "identical x, positive x0",
        "identical x, negative x0"
    ]



    name = "Analyst"

    def __init__(self, data, fig_name="figure.pdf"):

        self.data = data
        self.fig_name = fig_name

        self.sorted_data = None
        self.results = None
        self.n_trials = None

    def is_trial_with_losses_only(self, t):
        return self.data["x0"]["left"][t] < 0 and self.data["x0"]["right"][t] < 0

    def is_trial_with_gains_only(self, t):
        return self.data["x0"]["left"][t] > 0 and self.data["x0"]["right"][t] > 0

    def is_trial_with_fixed_p(self, t):

        return self.data["p"]["left"][t] == self.data["p"]["right"][t]

    def is_trial_with_fixed_x(self, t):

        return self.data["x0"]["left"][t] == self.data["x0"]["right"][t]

    def is_trial_with_best_option_on_left(self, t, condition):

        if condition in \
                ("identical p, positive vs negative x0",
                 "identical p, negative x0",
                 "identical p, positive x0"):
            return self.data["x0"]["left"][t] > self.data["x0"]["right"][t]

        elif condition == "identical x, negative x0":
            return self.data["p"]["left"][t] < self.data["p"]["right"][t]

        elif condition == "identical x, positive x0":
            return self.data["p"]["left"][t] > self.data["p"]["right"][t]

        else:
            raise Exception("Condition not understood.")

    def is_trial_a_hit(self, t, best_option):

        return self.data["choice"][t] == best_option

    def get_best_option(self, t, condition):

        best_is_left = self.is_trial_with_best_option_on_left(t, condition)
        return "left" if best_is_left else "right"

    def get_alternative(self, t, best_option):

        not_best_option = "left" if best_option != "left" else "right"
        alternative = (
            (self.data["p"][best_option][t], self.data["x0"][best_option][t]),
            (self.data["p"][not_best_option][t], self.data["x0"][not_best_option][t])
        )

        return alternative

    def which_type_of_control(self, t):

        type_of_control = None

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

        return type_of_control

    def sort_data(self):

        self.sorted_data = {i: {} for i in self.control_conditions}

        self.n_trials = len(self.data["p"]["left"])

        for t in range(self.n_trials):
            control_type = self.which_type_of_control(t)

            if control_type is None:
                continue

            best_option = self.get_best_option(t, control_type)
            is_a_hit = self.is_trial_a_hit(t, best_option)
            alternative = self.get_alternative(t, best_option)

            if alternative not in self.sorted_data[control_type].keys():
                self.sorted_data[control_type][alternative] = []

            self.sorted_data[control_type][alternative].append(is_a_hit)

    def get_results(self):

        self.results = {i: {} for i in self.control_conditions}

        for cond in self.control_conditions:

            print()
            print("Condition '{}'.".format(cond))

            data = self.sorted_data[cond]
            alternatives = sorted(list(data.keys()))

            n_trials = []
            means = []

            for i, alt in enumerate(alternatives):
                n = len(data[alt])
                mean = np.mean(data[alt])
                n_trials.append(n)

                self.results[cond][alt] = mean

                means.append(mean)

                print("{} {}: mean {}, n {}".format(i, alt, mean, n))

            perc_75, perc_25 = np.percentile(means, [75, 25])

            print()
            print("Number of pairs of lotteries", len(n_trials))
            print()
            print()
            print("The median of frequencies for {}: {:.02f} (IQR = {:.02f} -- {:.02f})".format(cond, np.median(means), perc_25, perc_75))
            print()
            print("Analysis of the number of trials")
            print()

            print("Min:", np.min(n_trials))
            print("Max:", np.max(n_trials))
            print("Median:", np.median(n_trials))
            print("Mean:", np.mean(n_trials))
            print("Std:", np.std(n_trials))
            print("Sum:", np.sum(n_trials))

    def plot(self):

        fig, ax = plt.subplots()

        n = len(self.control_conditions)

        names = ["Loss vs gains", "Diff. pos. $x_0$,\nSame p", "Diff. neg. $x_0$,\nSame p",
                 "Diff. p,\nSame pos. $x_0", "Diff. p,\nSame neg. $x_0"]

        colors = ["black", "C0", "C1", "C0", "C1"]
        positions = list(range(n))

        x_scatter = []
        y_scatter = []
        colors_scatter = []

        values_box_plot = []

        for i, cond in enumerate(self.control_conditions):

            values_box_plot.append([])

            for v in self.results[cond].values():

                # For box plot
                values_box_plot[-1].append(v)

                # For scatter
                y_scatter.append(v)
                x_scatter.append(i)
                colors_scatter.append(colors[i])

        ax.scatter(x_scatter, y_scatter, c=colors_scatter, s=30, alpha=1, linewidth=0.0, zorder=2)

        plt.xticks(positions, names, fontsize=8)

        bp = ax.boxplot(values_box_plot, positions=positions, labels=names, showfliers=False, zorder=1)

        for median in bp['medians']:
            median.set(color="black")
            median.set_alpha(0.5)

        for e in ['boxes','caps','whiskers']:
            for b in bp[e]:
                b.set_alpha(0.5)

        plt.xlabel("\nType of control")

        ax.set_ylim(0, 1.02)

        plt.ylabel("Success rate")

        # ax.set_aspect(2)
        # plt.legend()

        plt.tight_layout()

        plt.savefig(fname=self.fig_name)
        plt.close()

    def run(self):

        self.sort_data()
        self.get_results()
        self.plot()


def main(force=False):

    makedirs(folders["figures"], exist_ok=True)

    for monkey in ["Havane", "Gladys"]:

        print()
        print()
        print(monkey.upper())
        print()

        starting_point = starting_points[monkey]

        b = Backup(monkey, "data")
        data = b.load()

        fig_name = "{}/{}_{}.pdf" \
            .format(folders["figures"], monkey, get_script_name())

        if force is True or data is None:

            data = import_data(monkey=monkey, starting_point=starting_point, end_point=end_point)
            b.save(data)

        analyst = Analyst(data=data, fig_name=fig_name)
        analyst.run()


if __name__ == "__main__":
    main()
