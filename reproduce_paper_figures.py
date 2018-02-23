import os

import analysis


assert os.path.exists(analysis.parameters.database_path), \
    "Fatal: Could not find the database containing behavioral results! \n" \
    "Please give a look at the analysis parameters (analysis/parameters/parameters.py)."

analysis.modelling.main()
analysis.progress_histo.main()
analysis.exemplary_case.main()
analysis.preference_towards_risk_against_expected_value.main()
analysis.main_figures.main()


