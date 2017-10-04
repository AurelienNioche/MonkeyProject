import json

from os import path, mkdir

from data_management.data_manager import import_data
from analysis.progress_analyst import ProgressAnalyst
from analysis.analysis_parameters import starting_points, end_point


def check_progress():

    """
    Just produce a json file with the success rates per monkey.
    """

    for monkey in ["Havane", "Gladys"]:

        print("Analysis for {}".format(monkey))
        print()

        starting_point = starting_points[monkey]

        data = import_data(monkey=monkey, starting_point=starting_point, end_point=end_point)

        progress = dict()

        pa = ProgressAnalyst(p=data["p"], x0=data["x0"], x1=data["x1"], choice=data["choice"])

        for key in ProgressAnalyst.control_conditions:
            progress[key] = pa.analyse(key)

        folder = path.expanduser("~/Desktop/monkey_results_modelling")
        if not path.exists(folder):
            mkdir(folder)
        json_file = "{}/{}_progress.json".format(folder, monkey)

        with open(json_file, "w") as file:
            json.dump(progress, file)

        print()
        print("*" * 10)
        print()


if __name__ == "__main__":
    check_progress()
