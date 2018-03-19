import os

from utils import utils
import analysis


assert os.path.exists(analysis.parameters.database_path), \
    "Fatal: Could not find the database containing behavioral results! \n" \
    "Please take a look at the analysis parameters (analysis/parameters/parameters.py)."

analysis.modelling.main()
analysis.control_trials.main()
analysis.exemplary_case.main()
analysis.preference_towards_risk_against_expected_value.main()
analysis.main_figures.main()

utils.log("Done!", name="Reproduce paper figures")
utils.log("Path of the figures: {}".format(os.getcwd() + os.sep + analysis.parameters.folders["figures"]),
          name="Reproduce paper figures")


