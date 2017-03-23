import itertools as it
from multiprocessing import Pool, cpu_count
from os import path, mkdir

import numpy as np
from scipy.stats import binom

from data_management.data_manager import import_data
from utils.utils import today, log


class Model(object):

    labels = ['loss_aversion', 'negative_risk_aversion', 'positive_risk_aversion', 'probability_distortion', 'temp']

    reward_max = 3

    def __init__(self, parameters):

        self.parameters = dict()

        for i, j in zip(sorted(self.labels), parameters):
            self.parameters[i] = j

    def softmax(self, x1, x2):

        """Compute softmax values for each sets of scores in x."""
        # print("x", x)
        # return np.exp(x / tau) / np.sum(np.exp(x / tau), axis=0)
        return 1/(1+np.exp(-(1/self.parameters["temp"])*(x1-x2)))

    def u(self, x):

        """Compute utility for a single output considering a parameter of risk-aversion"""
        if x > 0:
            return (x/self.reward_max) ** (1-self.parameters["positive_risk_aversion"])
        else:
            return - ((np.absolute(x)/self.reward_max) ** self.parameters["negative_risk_aversion"]) \
                  / (1 - self.parameters["loss_aversion"])

    def U(self, L):

        """Compute utility for a lottery"""
        p, v = L[0], L[1]
        y = self.w(p) * self.u(v)

        return y

    def w(self, p):
        """Probability distortion"""

        return np.exp(-(-np.log(p))**self.parameters["probability_distortion"])

    def get_p(self, lottery_0, lottery_1):

        # print(lottery_0, lottery_1)
        U0, U1 = self.U(lottery_0), self.U(lottery_1)

        p_choose_U0 = self.softmax(U0, U1)

        return p_choose_U0


class ModelRunner(object):

    n_values_per_parameter = 10

    def __init__(self):

        self.possible_parameter_values = {
            "positive_risk_aversion": np.linspace(-1., 1., self.n_values_per_parameter),
            "negative_risk_aversion": np.linspace(-1., 1., self.n_values_per_parameter),
            "probability_distortion": np.linspace(0., 1., self.n_values_per_parameter),
            "loss_aversion": np.linspace(0.5, 1., self.n_values_per_parameter),
            "temp": np.linspace(0.05, 1., self.n_values_per_parameter)

        }

        assert sorted(Model.labels) == sorted(self.possible_parameter_values.keys())

    @staticmethod
    def compute(param):

        ps = []
        parameters, alternatives = param[0], param[1]
        model = Model(parameters)

        for l1, l2 in alternatives:

            p = model.get_p(l1, l2)
            ps.append(p)

        return ps

    def prepare_run(self, lotteries):

        parameters = np.array(list(
            it.product(*[self.possible_parameter_values[i] for i in sorted(self.possible_parameter_values.keys())])
        ))

        param_for_workers = []

        for i in parameters:

            param_for_workers.append([i, lotteries])

        return parameters, param_for_workers

    def run(self, alternatives):

        log("[ModelRunner] Launch run of model...")

        parameters, param_for_workers = self.prepare_run(alternatives)

        log("[ModelRunner] Number of different set of parameters: {}.".format(len(parameters[:, 0])))

        pool = Pool(processes=cpu_count())
        p = np.array(pool.map(self.compute, param_for_workers))

        log("[ModelRunner] Done!")
        return parameters, p


class LLS(object):

    def __init__(self, k, n, p):

        self.k = k
        self.n = n
        self.p = p

    def __call__(self, parameters_set):

        log_likelihood_sum = 0

        for i in range(len(self.n)):

            k, n, p = self.k[i], self.n[i], self.p[parameters_set, i]

            likelihood = binom.pmf(k=k, n=n, p=p)

            if likelihood == 0:
                log_likelihood_sum = - np.inf
                break

            log_likelihood = np.log(likelihood)
            log_likelihood_sum += log_likelihood

        return log_likelihood_sum


class LlsComputer(object):

    def __init__(self, k, n, p):

        self.k = k
        self.n = n
        self.p = p

    def run(self):

        log("[LlsComputer] Launch lls computation...")

        assert len(self.k) == len(self.n) == len(self.p[0, :]), \
            "len k: {}; len n: {}; len p: {}.".format(
                len(self.k), len(self.n), len(self.p[0, :]))

        pool = Pool(processes=cpu_count())

        lls_list = pool.map(

            LLS(self.k, self.n, self.p),
            np.arange(len(self.p[:, 0]))

        )

        lls_list = np.asarray(lls_list)

        log("[LlsComputer] Done!")

        return lls_list


class AlternativesNKGetter(object):

    def __init__(self, data):

        self.data = data

    def run(self):

        results = {}

        n_trials = len(self.data["p"]["left"])

        for t in range(n_trials):

            alternative = (
                (self.data["p"]["left"][t], self.data["x0"]["left"][t]),
                (self.data["p"]["right"][t], self.data["x0"]["right"][t])
            )

            reversed_alternative = alternative[::-1]

            reverse = False
            if alternative not in results.keys():
                if reversed_alternative not in results.keys():
                    results[alternative] = {"n": 0, "k": 0}
                else:
                    reverse = True

            if reverse:
                results[reversed_alternative]["n"] += 1
                results[reversed_alternative]["k"] += int(self.data["choice"][t] == "right")
            else:
                results[alternative]["n"] += 1
                results[alternative]["k"] += int(self.data["choice"][t] == "left")

        alternatives, n, k = [], [], []

        idx = 0
        for i, j in results.items():

            alternatives.append(i), n.append(j["n"]), k.append(j["k"])

            idx += 1

        return alternatives, n, k


def get_model_data(npy_files, alternatives, force=False):

    if all([path.exists(file) for file in npy_files.values()]) and not force:

        parameters = np.load(npy_files["parameters"])
        p = np.load(npy_files["p"])

    else:

        m = ModelRunner()
        parameters, p = m.run(alternatives=alternatives)

        np.save(npy_files["parameters"], parameters)
        np.save(npy_files["p"], p)

    return parameters, p


def get_monkey_data(monkey, npy_files, starting_point, end_point, force=False):

    if all([path.exists(file) for file in npy_files.values()]) and not force:

        alternatives = np.load(npy_files["alternatives"])
        n = np.load(npy_files["n"])
        k = np.load(npy_files["k"])

    else:

        data = import_data(monkey=monkey, starting_point=starting_point, end_point=end_point)

        alternatives_n_k_getter = AlternativesNKGetter(data)
        alternatives, n, k = alternatives_n_k_getter.run()

        np.save(npy_files["n"], n)
        np.save(npy_files["k"], k)
        np.save(npy_files["alternatives"], alternatives)

    return alternatives, n, k


def get_lls(n, k, p, npy_file, force=False):

    if path.exists(npy_file) and not force:

        lls = np.load(npy_file)

    else:

        lls_computer = LlsComputer(k=k, n=n, p=p)
        lls = lls_computer.run()

        np.save(npy_file, lls)

    return lls


def treat_results(monkey, lls_list, parameters_list):

    arg = np.argmax(lls_list)
    print("{}: ".format(monkey) + "".join(["{}: {:.2f}; ".format(k, v) for k, v in zip(sorted(Model.labels), parameters_list[arg])]))


def main():

    starting_point = "2016-02-01"
    end_point = today()

    folders = {
        "figures": path.expanduser("~/Desktop/monkey_figures"),
        "npy_files": path.expanduser("~/Desktop/monkey_npy_files")
    }

    for folder in folders.values():
        if not path.exists(folder): mkdir(folder)

    files = dict()
    files["model"] = {
        "p": "{}/{}.npy".format(folders["npy_files"], "model_p"),
        "parameters": "{}/{}.npy".format(folders["npy_files"], "model_parameters")
    }

    for monkey in ["Havane", "Gladys"]:

        files[monkey] = {
            "data": {
                "alternatives": "{}/{}_{}.npy".format(folders["npy_files"], monkey, "alternatives"),
                "n": "{}/{}_{}.npy".format(folders["npy_files"], monkey, "n"),
                "k": "{}/{}_{}.npy".format(folders["npy_files"], monkey, "k"),
            },
            "LLS": "{}/{}_{}.npy".format(folders["npy_files"], monkey, "lls")
        }

    monkeys = ["Gladys", "Havane"]

    for monkey in monkeys:

        print()
        log("[__main__] Processing for {}...".format(monkey))

        alternatives, n, k = get_monkey_data(
            monkey=monkey, starting_point=starting_point, end_point=end_point,
            npy_files=files[monkey]["data"])

        parameters, p = \
            get_model_data(npy_files=files["model"], alternatives=alternatives, force=True)

        lls_list = get_lls(
            k=k,
            n=n,
            p=p,
            npy_file=files[monkey]["LLS"], force=True)

        treat_results(monkey, lls_list, parameters)

        log("[__main__] Done!")


if __name__ == "__main__":

    main()
