import json

from analysis.utility_function_plot import UtilityFunctionPlot
from analysis.softmax_plot import SoftmaxPlot
from analysis.probability_distorsion_plot import ProbabilityDistortionPlot
from analysis.parameters import parameters


"""
To produce all figures based on parametrization *once the fitting has been done* 
"""


def main():

    for monkey in ["Havane", "Gladys"]:

        with open("{}/{}_fit.json".format(parameters.folders["fit"], monkey)) as f:
            data = json.load(f)

        pdp = ProbabilityDistortionPlot(monkey=monkey, alpha=data["probability_distortion"])
        pdp.plot()

        sp = SoftmaxPlot(monkey=monkey, temp=data["temp"])
        sp.plot()

        ufp = UtilityFunctionPlot(monkey=monkey, param=data)
        ufp.plot()


if __name__ == "__main__":
    main()
