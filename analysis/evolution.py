from os import path, mkdir
from pylab import np, plt
import itertools as it
import pickle
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

from data_management.data_manager import import_data
from analysis.analysis_parameters import folders
from analysis.modelling import AlternativesNKGetter, ModelRunner, LlsComputer, ProspectTheoryModel
from utils.utils import log


class Analyst:

    name = "Analyst"

    range_parameter_values = {
        "positive_risk_aversion": [-0.8, 0.8],
        "negative_risk_aversion": [-0.8, 0.8],
        "probability_distortion": [0.5, 1.],
        "loss_aversion": [-0.5, 0.5],
        "temp": [0.1, 0.3]
    }

    n_values_per_parameter = 10

    def __init__(self, data, monkey):

        self.data = data
        self.monkey = monkey
        self.n_dates = 0

    def sort_data(self):

        sorted_data = []

        for i, session_id in enumerate(np.unique(self.data["session"])):

            sorted_data.append({})

            idx = self.data["session"] == session_id

            for item in ["p", "x0"]:

                sorted_data[i][item] = dict()

                for side in ["left", "right"]:
                    sorted_data[i][item][side] = self.data[item][side][idx]

                sorted_data[i]["choice"] = self.data["choice"][idx]
            self.n_dates += 1

        return sorted_data

    @staticmethod
    def find_best_parameters(lls, parameters):

        arg = np.argmax(lls)

        best_parameters = None
        for i, param in enumerate(it.product(*parameters)):
            if i == arg:
                best_parameters = param
                break

        return dict([(k, v) for k, v in zip(sorted(ProspectTheoryModel.labels), best_parameters)])

    def run(self):

        log("Sort data for {}...".format(self.monkey), self.name)
        sorted_data = self.sort_data()
        log("Done.", self.name)

        pool = Pool(processes=cpu_count())
        best_parameters = pool.map(self.fit_data, sorted_data)
        # best_parameters = []
        # for i in tqdm(range(self.n_dates)):
        #
        #     best_parameters.append(
        #         self.fit_data(sorted_data[i]))

        return self.format_results(best_parameters)

    def fit_data(self, data):

        log("Extract alternatives, n and k...", self.name)
        alternatives_n_k_getter = AlternativesNKGetter(data)
        alternatives, n, k = alternatives_n_k_getter.run()
        log("Done.", self.name)

        log("Obtain data from model...", self.name)
        m = ModelRunner()
        m.run(alternatives=alternatives,
              n_values_per_parameter=self.n_values_per_parameter,
              range_parameter_values=self.range_parameter_values)  # , pool=pool)
        parameters = m.parameters_list
        p = m.p_list
        log("Done.", self.name)

        log("Obtain lls...", self.name)
        lls_computer = LlsComputer()
        lls_computer.prepare(k=k, n=n, p=p)
        lls = lls_computer.run()  # pool=pool)
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
        for i in range(self.n_dates):
            for key in sorted(ProspectTheoryModel.labels):
                new_results[key].append(results[i][key])

        new_results["n_dates"] = self.n_dates
        return new_results


class Backup:
    @classmethod
    def save(cls, data, monkey):
        backup_file = "{}/{}_evolution.p".format(folders["results"], monkey)

        with open(backup_file, "wb") as f:
            pickle.dump(data, f)


class Plot:
    @classmethod
    def plot(cls, monkey, data):

        if not path.exists(folders["figures"]):
            mkdir(folders["figures"])

        fig_name = "{}/{}_evolution.pdf" \
            .format(folders["figures"], monkey)

        x = np.arange(data["n_dates"])

        for key in sorted(ProspectTheoryModel.labels):

            plt.plot(x, data[key], label=key)

        plt.annotate('{} [n dates: {}]'.format(monkey, data["n_dates"]),
                    xy=(0, 0), xycoords='axes fraction', xytext=(0, 1.1))

        # Axis labels
        plt.xlabel("Date")
        plt.ylabel("Parameter value")

        plt.legend()

        plt.savefig(filename=fig_name)
        plt.close()


def main():

    starting_point = "2016-08-11"

    for monkey in ["Havane", "Gladys"]:

        data = import_data(monkey=monkey, starting_point=starting_point)

        analyst = Analyst(data=data, monkey=monkey)
        results = analyst.run()

        p = Plot()
        p.plot(monkey=monkey, data=results)

        b = Backup()
        b.save(monkey=monkey, data=results)


if __name__ == "__main__":

    main()
