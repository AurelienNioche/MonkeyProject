from os import makedirs
from pylab import np, plt
import itertools as it
import pickle
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

from data_management.data_manager import import_data
from analysis.modelling import AlternativesNKGetter, ModelRunner, LlsComputer, ProspectTheoryModel
from analysis.analysis_parameters import \
    folders, range_parameters, n_values_per_parameter, condition_evolution, starting_point

from utils.utils import log


class Analyst:

    name = "Analyst"

    def __init__(self, data, monkey):

        self.data = data
        self.monkey = monkey
        self.n_dates = 0

        self.sorted_data = []

    def sort_data(self, cond="day"):

        log("Sort data for {}...".format(self.monkey), self.name)

        if cond == "day":
            self.sort_data_per_day()

        elif cond == "beginning_vs_end":
            self.sort_data_beginning_vs_end()

        elif cond == "pool":
            self.sort_data_pool()

        else:
            raise Exception("Condition not understood.")

        log("Done.", self.name)

    def sort_data_beginning_vs_end(self):

        # A list of two dictionaries that will contain data, one for beginning of each session, one for end.
        self.sorted_data = [{k: [] if k == "choice" else {side: [] for side in ["left", "right"]}
                             for k in ["p", "x0", "choice"]} for i in range(2)]

        for i, session_id in enumerate(np.unique(self.data["session"])):

            idx = self.data["session"] == session_id
            part = len(self.data["choice"][idx]) // 2

            for item in ["p", "x0"]:
                for side in ["left", "right"]:
                    data = list(self.data[item][side][idx])
                    self.sorted_data[0][item][side] += data[:part]
                    self.sorted_data[1][item][side] += data[part:]

            data = list(self.data["choice"][idx])
            self.sorted_data[0]["choice"] += data[:part]
            self.sorted_data[1]["choice"] += data[part:]
            self.n_dates += 1

    def sort_data_pool(self, pool_size=10):

        self.n_dates = len(np.unique(self.data["session"]))

        n_groups = self.n_dates // pool_size

        # A list of dictionaries that will contain data, one for each pool.
        self.sorted_data = [
            {k: [] if k == "choice" else {side: [] for side in ["left", "right"]}
                for k in ["p", "x0", "choice"]} for i in range(n_groups)
        ]

        for i, session_id in enumerate(np.unique(self.data["session"])):
            group = i // pool_size
            if group >= n_groups:
                log("I will ignore the {} last sessions for having pool of equal size.".format(self.n_dates - i),
                    self.name)
                break
            idx = self.data["session"] == session_id

            for item in ["p", "x0"]:
                for side in ["left", "right"]:
                    self.sorted_data[group][item][side] += list(self.data[item][side][idx])

            self.sorted_data[group]["choice"] += list(self.data["choice"][idx])

    def sort_data_per_day(self):

        for i, session_id in enumerate(np.unique(self.data["session"])):

            self.sorted_data.append({})

            idx = self.data["session"] == session_id

            for item in ["p", "x0"]:

                self.sorted_data[i][item] = dict()

                for side in ["left", "right"]:
                    self.sorted_data[i][item][side] = self.data[item][side][idx]

            self.sorted_data[i]["choice"] = self.data["choice"][idx]
            self.n_dates += 1

    @staticmethod
    def find_best_parameters(lls, parameters):

        arg = np.argmax(lls)

        best_parameters = None
        for i, param in enumerate(it.product(*parameters)):
            if i == arg:
                best_parameters = param
                break

        return dict([(k, v) for k, v in zip(sorted(ProspectTheoryModel.labels), best_parameters)])

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


class Backup:

    def __init__(self, monkey, name):
        self.monkey = monkey
        self.backup_file = "{}/{}_{}.p".format(folders["results"], monkey, name)
        makedirs(folders["results"], exist_ok=True)

    def save(self, data):

        with open(self.backup_file, "wb") as f:
            pickle.dump(data, f)

    def load(self):

        try:
            with open(self.backup_file, "rb") as f:
                data = pickle.load(f)
                return data
        except:
            return


class Plot:
    @classmethod
    def plot(cls, monkey, data, name, cond):

        makedirs(folders["figures"], exist_ok=True)

        fig_name = "{}/{}_{}.pdf" \
            .format(folders["figures"], monkey, name)

        x = np.arange(data["n_group"])

        for key in sorted(ProspectTheoryModel.labels):

            plt.plot(x, data[key], linestyle='-', marker='o', label=key.replace("_", " ").capitalize())

        plt.annotate(
            '{} [n dates: {}]'.format(monkey, data["n_dates"]),
            xy=(0, 0), xycoords='axes fraction', xytext=(0, 1.1))

        if cond in ["day", "pool"]:

            # Axis labels
            plt.xlabel(cond.replace("_", " ").capitalize())

        elif cond == "beginning_vs_end":
            plt.xticks((0, 1), ("Beginning", "End"))
            plt.xlabel("Session")

        plt.ylabel("Parameter value")
        plt.ylim((-1, 1))

        plt.legend()

        plt.savefig(filename=fig_name)
        plt.close()


def main():

    name = "evolution_param_{}".format(condition_evolution)

    for monkey in ["Havane", "Gladys"]:
        b = Backup(monkey=monkey, name=name)

        results = None  # b.load()
        if results is None:
            data = import_data(monkey=monkey, starting_point=starting_point)

            analyst = Analyst(data=data, monkey=monkey)
            analyst.sort_data(condition_evolution)
            results = analyst.run()
            b.save(data=results)

        p = Plot()
        p.plot(monkey=monkey, data=results, name=name, cond=condition_evolution)


if __name__ == "__main__":

    main()
