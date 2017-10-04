from os import makedirs
from pylab import plt

from data_management.data_manager import import_data
from data_management.data_sorter import sort_data

from analysis.analysis_parameters import folders

from analysis.progress_analyst import ProgressAnalyst


class ProgressPerArbitraryPool(object):

    def __init__(self, sorted_data):

        self.sorted_data = sorted_data

        self.progress = dict([(k, []) for k in ProgressAnalyst.control_conditions])

    def run(self):

        print("Analyse...\n")

        for i, data in enumerate(self.sorted_data):

            if "dates" in data.keys():
                print("Pool {}".format(i))
                print("Dates: from {} to {}".format(data["dates"][0], data["dates"][-1]))
            pa = ProgressAnalyst(p=data["p"], x0=data["x0"], choice=data["choice"])
            for key in self.progress:
                self.progress[key].append(pa.analyse(key))

            print("\n" + "*" * 10 + "\n")

        return self.progress


class Plot:

    fig_size = (25, 12)
    marker = 'o'
    line_width = 2
    bbox_to_anchor = (1, 0.5)
    loc = 'center left'

    def __init__(self, monkey, results, cond=""):

        self.monkey = monkey
        self.results = results
        self.cond = cond

        makedirs(folders["figures"], exist_ok=True)
        self.fig_name = self.get_fig_name()

    def get_fig_name(self):
        return "{}/{}_progress{}.pdf".format(folders["figures"], self.monkey, self.cond.capitalize())

    def plot(self):

        plt.figure(figsize=self.fig_size)
        ax = plt.subplot(111)

        for key in self.results:

            plt.plot(range(len(self.results[key])), self.results[key],
                     marker=self.marker, label=key, linewidth=self.line_width)

            plt.ylim([-0.01, 1.01])
            plt.ylabel("Success rate")
            plt.xlabel("t")

        ax.set_title(self.monkey)

        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(loc=self.loc, bbox_to_anchor=self.bbox_to_anchor)

        plt.savefig(self.fig_name)
        plt.close()


def main():

    starting_point = "2016-12-01"  # "2017-03-01"

    sort_type = "pool"

    for monkey in ["Havane", "Gladys"]:

        # Get data and sort it
        data = import_data(monkey=monkey, starting_point=starting_point)
        sorted_data = sort_data(data=data, sort_type=sort_type)

        pr = ProgressPerArbitraryPool(sorted_data=sorted_data)
        results = pr.run()

        pl = Plot(monkey=monkey, results=results, cond=sort_type)
        pl.plot()


if __name__ == "__main__":

    main()
