import json

from os import path, mkdir

from data_management.data_manager import import_data
from analysis.check_progress import ProgressAnalyst
from analysis.analysis_parameters import starting_point, end_point


def check_progress():

    for monkey in ["Havane", "Gladys"]:

        print("Analysis for {}".format(monkey))
        print()

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
