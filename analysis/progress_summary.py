import json
import os

from data_management.data_manager import import_data
from analysis.tools.progress_analyst import ProgressAnalyst
from analysis.parameters import parameters

"""
Supp: Produce a json file with summarizes the success rates per monkey.
"""


def main():

    for monkey in ["Havane", "Gladys"]:

        print("Analysis for {}".format(monkey))
        print()

        starting_point = parameters.starting_points[monkey]

        data = import_data(monkey=monkey, starting_point=starting_point,
                           end_point=parameters.end_point, database_path=parameters.database_path)

        progress = dict()

        pa = ProgressAnalyst(p=data["p"], x0=data["x0"], choice=data["choice"])

        for key in ProgressAnalyst.control_conditions:
            progress[key] = pa.analyse(key)

        folder = parameters.folder_path
        os.makedirs(folder, exist_ok=True)

        json_file = "{}/{}_progress.json".format(folder, monkey)

        with open(json_file, "w") as file:
            json.dump(progress, file)

        print()
        print("*" * 10)
        print()


if __name__ == "__main__":
    main()
