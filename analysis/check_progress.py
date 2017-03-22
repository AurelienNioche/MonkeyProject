from collections import OrderedDict
from os import path
from pylab import np, plt

from data_management.data_manager import import_data


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


def check_progress():

    starting_point = "2016-08-11"

    for monkey in ["Havane", "Gladys"]:

        print("Analysis for {}".format(monkey))
        print()

        data = import_data(monkey=monkey, starting_point=starting_point)

        progress = OrderedDict()

        for key in ProgressAnalyst.control_conditions:
            progress[key] = []

        print(progress)
        for session_id in np.unique(data["session"]):

            session_p = dict()
            session_x0 = dict()
            session_x1 = dict()

            for side in ["left", "right"]:

                session_p[side] = data["p"][side][data["session"] == session_id]
                session_x0[side] = data["x0"][side][data["session"] == session_id]
                session_x1[side] = data["x1"][side][data["session"] == session_id]

            session_choice = data["choice"][data["session"] == session_id]

            print()
            pa = ProgressAnalyst(p=session_p, x0=session_x0, x1=session_x1, choice=session_choice)
            for key in progress:
                progress[key].append(pa.analyse(key))

            print()
            print("*" * 10)
            print()

        plt.figure(figsize=(25, 12))
        ax = plt.subplot(111)

        for key in progress:

            plt.plot(np.unique(data["session"]) + 1, progress[key], label=key, linewidth=2)
            plt.xticks(np.arange(len(np.unique(data["session"]))) + 1)
            plt.ylim([-0.01, 1.01])
            plt.ylabel("Success rate")
            plt.xlabel("Day")

        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

        ax.set_title(monkey)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.savefig(path.expanduser("~/Desktop/{}_progress.pdf".format(monkey)))
        plt.close()


if __name__ == "__main__":

    check_progress()
