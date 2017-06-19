import itertools as it
from multiprocessing import Pool, cpu_count
from os import path, mkdir

import numpy as np
import json
from scipy.stats import binom

from analysis.analysis_parameters import folders, starting_point, end_point
from data_management.data_manager import import_data
from utils.utils import log


class ProspectTheoryModel(object):

    labels = ['loss_aversion', 'negative_risk_aversion', 'positive_risk_aversion', 'probability_distortion', 'temp']

    absolute_reward_max = 3

    def __init__(self, parameters):

        self.parameters = dict()

        for i, j in zip(sorted(self.labels), parameters):
            self.parameters[i] = j

        # self.norm = self.absolute_reward_max / (1 - self.parameters["loss_aversion"])

    def softmax(self, x1, x2):
        """Compute softmax values for each sets of scores in x."""
        # print("x", x)
        # return np.exp(x / tau) / np.sum(np.exp(x / tau), axis=0)
        return 1/(1+np.exp(-(1/self.parameters["temp"])*(x1-x2)))

    def u(self, x):
        """Compute utility for a single output considering a parameter of risk-aversion"""

        if x > 0:
            v = (x/self.absolute_reward_max) ** (1 - self.parameters["positive_risk_aversion"])

            if self.parameters["loss_aversion"] > 0:
                v = (1 - self.parameters["loss_aversion"]) * v

        else:
            v = - (abs(x)/self.absolute_reward_max) ** (1 + self.parameters["negative_risk_aversion"])

            if self.parameters["loss_aversion"] < 0:
                v = (1 + self.parameters["loss_aversion"]) * v

        assert 0. <= abs(v) <= 1., print("v", v, "; x", x,
                                         "; neg", self.parameters["negative_risk_aversion"],
                                         "; pos", self.parameters["positive_risk_aversion"])
        return v

    def U(self, L):
        """Compute utility for a lottery"""

        p, v = L[0], L[1]
        y = self.w(p) * self.u(v)

        return y

    def w(self, p):
        """Probability distortion"""

        return np.exp(-(-np.log(p))**self.parameters["probability_distortion"])

    def get_p(self, lottery_0, lottery_1):

        """ Compute the probability of choosing lottery '0' against lottery '1' """

        # print(lottery_0, lottery_1)
        U0, U1 = self.U(lottery_0), self.U(lottery_1)

        p_choose_U0 = self.softmax(U0, U1)

        return p_choose_U0


class ModelRunner(object):

    name = "ModelRunner"

    alternatives = None

    parameters_list = None
    n_set_parameters = None

    p_list = None

    @classmethod
    def prepare(cls, alternatives):

        cls.alternatives = alternatives

        cls.prepare_parameters_list()

    @classmethod
    def prepare_parameters_list(cls):

        n_values_per_parameter = 10

        possible_parameter_values = {
            "positive_risk_aversion": np.linspace(-1., 1., n_values_per_parameter),
            "negative_risk_aversion": np.linspace(-1., 1., n_values_per_parameter),
            "probability_distortion": np.linspace(0., 1., n_values_per_parameter),
            "loss_aversion": np.linspace(-0.5, 0.5, n_values_per_parameter),
            "temp": np.linspace(0.05, 0.5, n_values_per_parameter)
        }

        assert sorted(possible_parameter_values.keys()) == ProspectTheoryModel.labels

        cls.n_set_parameters = n_values_per_parameter ** len(possible_parameter_values)
        cls.parameters_list = [possible_parameter_values[i] for i in sorted(possible_parameter_values.keys())]

    @classmethod
    def compute(cls, parameters):

        ps = np.zeros(len(cls.alternatives))
        model = ProspectTheoryModel(parameters)

        for i, (l1, l2) in enumerate(cls.alternatives):

            ps[i] = model.get_p(l1, l2)

        return ps

    @classmethod
    def run(cls, alternatives):

        cls.prepare(alternatives)

        log("Launch run of model...", cls.name)

        log("Number of different set of parameters: {}.".format(cls.n_set_parameters), cls.name)

        pool = Pool(processes=cpu_count())

        cls.p_list = np.array(pool.map(cls.compute, it.product(*cls.parameters_list)))

        log("Done!", cls.name)


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

    name = "LlsComputer"

    def __init__(self, k, n, p):

        self.k = k
        self.n = n
        self.p = p

    def run(self):

        log("Launch lls computation...", self.name)

        assert len(self.k) == len(self.n) == len(self.p[0, :]), \
            "len k: {}; len n: {}; len p: {}.".format(
                len(self.k), len(self.n), len(self.p[0, :]))

        pool = Pool(processes=cpu_count())

        lls_list = pool.map(

            LLS(self.k, self.n, self.p),
            np.arange(len(self.p[:, 0]))

        )

        lls_list = np.asarray(lls_list)

        log("Done!", self.name)

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

        parameters_it = np.load(npy_files["parameters"])
        p = np.load(npy_files["p"])

        return parameters_it, p

    else:

        m = ModelRunner()
        m.run(alternatives)

        np.save(npy_files["parameters"], m.parameters_list)
        np.save(npy_files["p"], m.p_list)

        return m.parameters_list, m.p_list


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


def treat_results(monkey, lls_list, parameters, json_file):

    arg = np.argmax(lls_list)

    best_parameters = None
    for i, param in enumerate(it.product(*parameters)):
        if i == arg:
            best_parameters = param
            break
    print(best_parameters)

    msg = "{}: ".format(monkey) + \
        "".join(["{}: {:.2f}; ".format(k, v) for k, v in zip(sorted(ProspectTheoryModel.labels), best_parameters)])
    print(msg)

    result = dict([(k, v) for k, v in zip(sorted(ProspectTheoryModel.labels), best_parameters)])
    with open(json_file, "w") as file:
        json.dump(result, file)


def main():

    for folder in folders.values():
        if not path.exists(folder):
            mkdir(folder)

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
            "LLS": "{}/{}_{}.npy".format(folders["npy_files"], monkey, "lls"),
            "result": "{}/{}_{}.json".format(folders["results"], monkey, "result")
        }

    monkeys = ["Gladys", "Havane"]

    for monkey in monkeys:

        print()
        log("Processing for {}...".format(monkey), name="__main__")

        log("Getting experimental data for {}...".format(monkey), name="__main__")
        alternatives, n, k = get_monkey_data(
            monkey=monkey, starting_point=starting_point, end_point=end_point,
            npy_files=files[monkey]["data"], force=True)

        log("Getting model data for {}...".format(monkey), name="__main__")
        parameters, p = \
            get_model_data(
                npy_files=files["model"], alternatives=alternatives, force=True)

        log("Getting statistical data for {}...".format(monkey), name="__main__")
        lls_list = get_lls(
            k=k,
            n=n,
            p=p,
            npy_file=files[monkey]["LLS"], force=True)

        treat_results(
            monkey=monkey, lls_list=lls_list, parameters=parameters,
            json_file=files[monkey]["result"])

        log("Done!", name="__main__")


if __name__ == "__main__":

    main()
