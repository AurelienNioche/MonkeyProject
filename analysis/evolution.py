from os import makedirs
from pylab import np, plt
import itertools as it
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

from data_management.data_manager import import_data
from data_management.data_sorter import sort_data

from analysis.backup import Backup
from analysis.modelling import AlternativesNKGetter, ModelRunner, LlsComputer, ProspectTheoryModel
from analysis.analysis_parameters import \
    folders, range_parameters, n_values_per_parameter, condition_evolution

from utils.utils import log


class Analyst:

    name = "Analyst"

    def __init__(self, sorted_data, n_dates):

        self.n_dates = n_dates
        self.sorted_data = sorted_data

    def run(self, multi=True):

        if multi:
            pool = Pool(processes=cpu_count()-1)
            best_parameters = pool.map(self.fit_data, self.sorted_data)

        else:
            best_parameters = []
            for i in tqdm(range(len(self.sorted_data))):

                best_parameters.append(
                    self.fit_data(self.sorted_data[i]))

        return self.format_results(best_parameters)

    @staticmethod
    def find_best_parameters(lls, parameters):

        arg = np.argmax(lls)

        best_parameters = None
        for i, param in enumerate(it.product(*parameters)):
            if i == arg:
                best_parameters = param
                break

        return dict([(k, v) for k, v in zip(sorted(ProspectTheoryModel.labels), best_parameters)])

    def fit_data(self, data):

        log("Extract alternatives, n and k...", self.name)
        alternatives_n_k_getter = AlternativesNKGetter(data)
        alternatives, n, k = alternatives_n_k_getter.run()
        log("Done.", self.name)

        log("Obtain data from model...", self.name)
        m = ModelRunner()
        m.run(alternatives=alternatives,
              n_values_per_parameter=n_values_per_parameter,
              range_parameters=range_parameters)

        parameters = m.parameters_list
        p = m.p_list
        log("Done.", self.name)

        log("Obtain lls...", self.name)
        lls_computer = LlsComputer()
        lls_computer.prepare(k=k, n=n, p=p)
        lls = lls_computer.run()
        log("Done.", self.name)

        log("Find best parameters", self.name)
        best_fit = self.find_best_parameters(lls=lls, parameters=parameters)
        log("Done.", self.name)

        log("Best fit is: {}.".format(best_fit), self.name)

        return best_fit

    def format_results(self, results):

        new_results = {
            key: [] for key in sorted(ProspectTheoryModel.labels)
        }
        for i in range(len(self.sorted_data)):
            for key in sorted(ProspectTheoryModel.labels):
                new_results[key].append(results[i][key])

        new_results["n_dates"] = self.n_dates
        new_results["n_group"] = len(self.sorted_data)
        return new_results


class Plot:

    fig_size = (25, 12)
    marker = 'o'
    line_width = 2
    bbox_to_anchor = (1, 0.5)
    loc = 'center left'

    @classmethod
    def plot(cls, monkey, data, name, cond):

        makedirs(folders["figures"], exist_ok=True)

        plt.figure(figsize=cls.fig_size)
        ax = plt.subplot(111)

        fig_name = "{}/{}_{}.pdf" \
            .format(folders["figures"], monkey, name)

        x = np.arange(data["n_group"])

        for key in sorted(ProspectTheoryModel.labels):

            ax.plot(x, data[key], linestyle='-', marker='o', label=key.replace("_", " ").capitalize())

        ax.annotate(
            '{} [n dates: {}]'.format(monkey, data["n_dates"]),
            xy=(0, 0), xycoords='axes fraction', xytext=(0, 1.1))

        if cond in ["day", "pool"]:

            # Axis labels
            ax.set_xlabel(cond.replace("_", " ").capitalize())

        elif cond == "beginning_vs_end":
            plt.xticks((0, 1), ("Beginning", "End"))
            plt.xlabel("Session")

        ax.set_ylabel("Parameter value")
        ax.set_ylim((-1, 1))

        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(loc=cls.loc, bbox_to_anchor=cls.bbox_to_anchor)

        plt.savefig(filename=fig_name)
        plt.close()


def main(just_do_graphs=True):

    kind_of_analysis = "evolution_param_{}".format(condition_evolution)

    starting_point = "2016-12-01"

    for monkey in ["Havane", "Gladys"]:

        b = Backup(monkey=monkey, kind_of_analysis=kind_of_analysis)

        if just_do_graphs:
            results = b.load()
        else:
            results = None

        if results is None:

            # Get data and sort it
            data = import_data(monkey=monkey, starting_point=starting_point)
            sorted_data = sort_data(data=data, sort_type=condition_evolution)

            analyst = Analyst(sorted_data=sorted_data, n_dates=len(data["session"]), monkey=monkey)

            results = analyst.run()
            b.save(data=results)

        p = Plot()
        p.plot(monkey=monkey, data=results, name=kind_of_analysis, cond=condition_evolution)


if __name__ == "__main__":

    main()
