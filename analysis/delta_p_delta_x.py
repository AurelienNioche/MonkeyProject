from pylab import np, plt
from scipy.optimize import curve_fit
from os import path, mkdir

from data_management.data_manager import import_data
from utils.utils import log
from analysis.analysis_parameters import folders, starting_point, end_point


class Plot(object):

    axis_label_font_size = 12

    def __init__(self, fig_name):

        self.fig_name = fig_name

    def plot(self, results, monkey, condition):

        fig, ax = plt.subplots()

        x_data = results["delta_p"]
        y_data = results["delta_x"]
        z_data = results["choice"]

        n_trials = results["n_trials"]

        plt.scatter(x_data, y_data, c=z_data, marker="s", s=1500)

        c_bar = plt.colorbar()

        c_bar.ax.set_ylabel('Choice')

        ax.set_xlim(-0.85, 0.85)
        ax.set_ylim(-2.5, 2.5)
        ax.set_xticks(np.arange(-0.75, 0.76, 0.25))
        ax.set_aspect(0.25)

        ax.annotate('{}, {} [n trials: {}]'.format(monkey, condition.replace("_", " "), n_trials),
                    xy=(0, 0), xycoords='axes fraction', xytext=(0, 1.1))

        # Axis labels
        plt.xlabel("$\delta p$",
                   fontsize=self.axis_label_font_size)
        plt.ylabel("$\delta q$",
                   fontsize=self.axis_label_font_size)

        plt.savefig(filename=self.fig_name)
        plt.close()


class Analyst(object):

    name = "Analyst"

    def __init__(self, data, condition):

        self.data = data
        self.condition = condition
        assert self.condition in ["with_gains_only", "with_losses_only"]

    def is_trial_with_losses_only(self, t):

        return self.data["x0"]["left"][t] < 0 and self.data["x0"]["right"][t] < 0

    def is_trial_with_gains_only(self, t):

        return self.data["x0"]["left"][t] > 0 and self.data["x0"]["right"][t] > 0

    def get_sorted_data(self):

        sorted_data = {}

        n_trials = len(self.data["p"]["left"])

        for t in range(n_trials):

            delta = {}

            if (not self.condition == "with_gains_only" or self.is_trial_with_gains_only(t)) and \
                    (not self.condition == "with_losses_only" or self.is_trial_with_losses_only(t)):

                for i in ["x0", "p"]:
                    delta[i] = self.data[i]["left"][t] - self.data[i]["right"][t]

                choose_left = int(self.data["choice"][t] == "left")

                key = tuple(delta.items())
                if key not in sorted_data.keys():
                    sorted_data[key] = []

                sorted_data[key].append(choose_left)

        return sorted_data

    @staticmethod
    def compute(sorted_data):

        delta_p = []
        delta_x = []
        choice = []
        n_trials = 0

        for key, value in sorted_data.items():

            delta = dict(key)
            delta_p.append(delta["p"])
            delta_x.append(delta["x0"])
            choice.append(np.mean(value))

            n_trials += len(value)

        return {"delta_p": delta_p, "delta_x": delta_x, "choice": choice, "n_trials": n_trials}

    def run(self):

        sorted_data = self.get_sorted_data()
        return self.compute(sorted_data)


def main():

    if not path.exists(folders["figures"]):
        mkdir(folders["figures"])

    for monkey in ["Havane", "Gladys"]:

        data = import_data(monkey=monkey, starting_point=starting_point, end_point=end_point)

        for condition in ["with_gains_only", "with_losses_only"]:

            analyst = Analyst(data=data, condition=condition)
            results = analyst.run()

            log("N trials: {}".format(results["n_trials"]), "__main__")

            fig_name = "{}/{}_delta_p_delta_x_{}.pdf"\
                .format(folders["figures"], monkey, condition)

            plot = Plot(fig_name=fig_name)
            plot.plot(results, monkey, condition)


if __name__ == "__main__":

    main()
