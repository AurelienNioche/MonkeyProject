from os import path, mkdir
from pylab import np, plt

from data_management.data_manager import import_data
from analysis.analysis_parameters import folders


class ProgressAnalyst(object):

    control_conditions = [
        "identical p, negative x0",
        "identical p, positive x0",
        "identical p, positive vs negative x0",
        "identical x, negative x0",
        "identical x, positive x0"
    ]

    def __init__(self, p, x0, x1, choice):

        self.p = p
        self.x0 = x0
        self.x1 = x1
        self.choice = choice
        self.trials_id = np.arange(len(self.p["left"]))

        self.dict_functions = dict()
        for key in self.control_conditions:
            self.dict_functions[key] = getattr(self, 'analyse_{}'.format(key.replace(" ", "_").replace(",", "")))

    def analyse(self, condition):

        return self.dict_functions[condition]()

    def analyse_identical_p_negative_x0(self):

        n = 0
        hit = 0

        assert len(self.choice) == len(self.trials_id)

        for i in self.trials_id:

            if self.p["left"][i] == self.p["right"][i] and self.x1["left"][i] == self.x1["right"][i] \
                    and self.x0["left"][i] < 0 and self.x0["right"][i] < 0:

                n += 1

                if (self.choice[i] == "left") == (self.x0["left"][i] > self.x0["right"][i]):

                    hit += 1
        if n:

            print("Success rate with identical p, negative x0: {:.2f}".format(hit / n))
            return hit / n

    def analyse_identical_p_positive_x0(self):

        n = 0
        hit = 0

        assert len(self.choice) == len(self.trials_id)

        for i in self.trials_id:

            if self.p["left"][i] == self.p["right"][i] and self.x1["left"][i] == self.x1["right"][i] \
                    and self.x0["left"][i] > 0 and self.x0["right"][i] > 0:

                n += 1

                if (self.choice[i] == "left") == (self.x0["left"][i] > self.x0["right"][i]):

                    hit += 1
        if n:
            print("Success rate with identical p, positive x0: {:.2f}".format(hit / n))
            return hit / n

    def analyse_identical_p_positive_vs_negative_x0(self):

        n = 0
        hit = 0

        assert len(self.choice) == len(self.trials_id)

        for i in self.trials_id:

            if self.p["left"][i] == self.p["right"][i] and self.x1["left"][i] == self.x1["right"][i] \
                    and (self.x0["left"][i] > 0 > self.x0["right"][i] or
                         self.x0["left"][i] < 0 < self.x0["right"][i]):

                n += 1

                if (self.choice[i] == "left") == (self.x0["left"][i] > self.x0["right"][i]):

                    hit += 1

        if n:

            print("Success rate with identical p, positive vs negative x0: {:.2f}".format(hit / n))
            return hit / n

    def analyse_identical_x_positive_x0(self):

        n = 0
        hit = 0

        for i in self.trials_id:

            if self.x0["left"][i] == self.x0["right"][i] and self.x1["left"][i] == self.x1["right"][i] and \
                    self.x0["left"][i] > 0:

                n += 1

                if (self.choice[i] == "left") == (self.p["left"][i] > self.p["right"][i]):
                    hit += 1
        if n:
            print("Success rate with identical x, positive x0: {:.2f}".format(hit / n))
            return hit / n

    def analyse_identical_x_negative_x0(self):

        n = 0
        hit = 0

        for i in self.trials_id:

            if self.x0["left"][i] == self.x0["right"][i] and self.x1["left"][i] == self.x1["right"][i] and \
                    self.x0["left"][i] < 0:

                n += 1

                if (self.choice[i] == "left") == (self.p["left"][i] < self.p["right"][i]):
                    hit += 1

        if n:
            print("Success rate with identical x, negative x0: {:.2f}".format(hit / n))
            return hit / n


class ProgressPerSession(object):

    def __init__(self, starting_point, monkey):

        self.monkey = monkey
        self.starting_point = starting_point

        self.progress = dict([(k, []) for k in ProgressAnalyst.control_conditions])
        self.data = import_data(monkey=self.monkey, starting_point=self.starting_point)

        self.fig_name = self.get_fig_name()

    def get_fig_name(self):

        if not path.exists(folders["figures"]):
            mkdir(folders["figures"])

        return "{}/{}_progress.pdf".format(folders["figures"], self.monkey)

    def analyse(self):

        print("Analysis for {}".format(self.monkey))
        print()

        for session_id in np.unique(self.data["session"]):

            session_p = dict()
            session_x0 = dict()
            session_x1 = dict()

            for side in ["left", "right"]:
                session_p[side] = self.data["p"][side][self.data["session"] == session_id]
                session_x0[side] = self.data["x0"][side][self.data["session"] == session_id]
                session_x1[side] = self.data["x1"][side][self.data["session"] == session_id]

            session_choice = self.data["choice"][self.data["session"] == session_id]

            print()
            pa = ProgressAnalyst(p=session_p, x0=session_x0, x1=session_x1, choice=session_choice)
            for key in self.progress:
                self.progress[key].append(pa.analyse(key))

            print()
            print("*" * 10)
            print()

    def plot(self):

        plt.figure(figsize=(25, 12))
        ax = plt.subplot(111)

        for key in self.progress:

            plt.plot(np.unique(self.data["session"]) + 1, self.progress[key], label=key, linewidth=2)
            plt.xticks(np.arange(len(np.unique(self.data["session"]))) + 1)
            plt.ylim([-0.01, 1.01])
            plt.ylabel("Success rate")
            plt.xlabel("Session")

        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

        ax.set_title(self.monkey)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.savefig(self.fig_name)
        plt.close()


def main():

    starting_point = "2016-08-11"

    for monkey in ["Havane", "Gladys"]:

        pps = ProgressPerSession(monkey=monkey, starting_point=starting_point)
        pps.analyse()
        pps.plot()


if __name__ == "__main__":

    main()
