import json

from analysis.utility_function_plot import UtilityFunctionPlot
from analysis.softmax_plot import SoftmaxPlot
from analysis.probability_distorsion_plot import ProbabilityDistortionPlot
from analysis.analysis_parameters import folders


def main():

    for monkey in ["Havane", "Gladys"]:

        with open("{}/{}_result.json".format(folders["results"], monkey)) as f:
            data = json.load(f)

        pdp = ProbabilityDistortionPlot(monkey=monkey, alpha=data["probability_distortion"])
        pdp.plot()

        sp = SoftmaxPlot(monkey=monkey, temp=data["temp"])
        sp.plot()

        ufp = UtilityFunctionPlot(monkey=monkey, parameters=data)
        ufp.plot()


if __name__ == "__main__":
    main()
