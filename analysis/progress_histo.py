from os import makedirs
from pylab import np, plt
from scipy.stats import sem

from data_management.data_manager import import_data
from data_management.data_sorter import sort_data

from analysis.analysis_parameters import folders
from analysis.progress_analyst import ProgressAnalyst
from analysis.backup import Backup


class ProgressHist(object):

    def __init__(self, sorted_data):

        self.sorted_data = sorted_data

        self.progress = dict([(k, []) for k in ProgressAnalyst.control_conditions])
        progress2 = {k:[] for k in ProgressAnalyst.control_conditions}

        assert progress2 == self.progress

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

    fig_size = None
    marker = 'o'
    line_width = 2
    bbox_to_anchor = (1, 0.5)
    loc = 'center left'

    def __init__(self, monkey, results):

        self.monkey = monkey
        self.results = results

        makedirs(folders["figures"], exist_ok=True)
        self.fig_name = self.get_fig_name()

    def get_fig_name(self):
        return "{}/{}_progressHist.pdf".format(folders["figures"], self.monkey)

    def plot(self):

        plt.figure(figsize=self.fig_size)
        ax = plt.subplot(111)

        pos_amounts = [
            'identical p, positive x0',
            'identical x, positive x0'
        ]
        neg_amounts = [
            'identical p, negative x0',
            'identical x, negative x0'
        ]

        labels = ['Identical p\n(diff amounts)', 'Identical amount\n(diff p)', 'Negative vs positive amount']

        other_cond = 'identical p, positive vs negative x0'

        n = len(pos_amounts)

        means_1 = [np.mean([i for i in self.results[key] if i]) for key in pos_amounts]
        means_2 = [np.mean([i for i in self.results[key] if i]) for key in neg_amounts]

        mean_3 = np.mean([i for i in self.results[other_cond] if i])

        sem_1 = [sem([i for i in self.results[key] if i]) for key in pos_amounts]
        sem_2 = [sem([i for i in self.results[key] if i]) for key in neg_amounts]

        sem_3 = sem([i for i in self.results[other_cond] if i])

        ind = np.arange(n)  # the x locations for the groups
        width = 0.35  # the width of the bars

        rct_1 = ax.bar(ind, means_1, width, color='C0', yerr=sem_1)
        rct_2 = ax.bar(ind + width, means_2, width, color='C1', yerr=sem_2)

        ax.bar(n + width / 2,  mean_3, width, color='C3', yerr=sem_3)

        ax.set_ylabel('Success rate')
        ax.set_ylim([0, 1])
        ax.set_title(self.monkey)

        ax.set_xticks(np.arange(n+1) + width / 2)
        ax.set_xticklabels(labels=labels)

        ax.legend((rct_1[0], rct_2[0]), ('Positive amounts', 'Negative amounts'))

        plt.savefig(self.fig_name)
        plt.close()


def main():

    starting_points = \
        {
            "Havane": "2017-03-03",
            "Gladys": "2017-03-31"
        }  # "2016-12-01", "2017-03-01"

    for monkey in ["Havane", "Gladys"]:

        starting_point = starting_points[monkey]

        b = Backup(monkey, "progressHist")
        sorted_data = b.load()

        if sorted_data is None:  # or True:  # add 'or True' if you want to force the importation of data:
            raw_data = import_data(monkey=monkey, starting_point=starting_point)
            sorted_data = sort_data(raw_data, sort_type="day")
            b.save(sorted_data)

        pr = ProgressHist(sorted_data=sorted_data)
        results = pr.run()

        pl = Plot(monkey=monkey, results=results)
        pl.plot()


if __name__ == "__main__":

    main()
