from os import path
# from utils.utils import today

""" 
Parameters for analysis: where is the database, and so on
"""

# Path of the behavioral results
database_path = path.expanduser("~/GoogleDrive/MonkeyTaskResults/results_2017_09_31.db")

# Path for all the analysis results
folder_path = "results_analysis"
# path.expanduser("~/GoogleDrive/SBGProject/MonkeyProject-master/MonkeyResults2017-10-04")

# Subfolders for figures, fit, and other data files produced for analysis
folders = {key: folder_path + "/" + key for key in ["figures", "fit", "npy", "pickle"]}

# Range of parameters for the fit
range_parameters = {
    "positive_risk_aversion": [-0.9, 0.9],
    "negative_risk_aversion": [-0.9, 0.9],
    "probability_distortion": [0.4, 1.],
    "loss_aversion": [-1.0, 0.5],
    "temp": [0.1, 0.5]
}

# From where data are taken into account
starting_points = \
    {
        "Havane": "2017-03-03",
        "Gladys": "2017-03-31"
    }  # "2016-12-01", "2017-03-01"

# N values that will be tested for each parameter during the estimations of best values for the fit
n_values_per_parameter = 10

end_point = "2017-10-01"  # today()

