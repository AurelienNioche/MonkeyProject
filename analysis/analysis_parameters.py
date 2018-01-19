from os import path
from utils.utils import today

folder_path = path.expanduser("~/GoogleDrive/SBGProject/MonkeyProject-master/MonkeyResults2017-10-04")

folders = {key: folder_path + "/" + key for key in ["figures", "fit", "npy_files", "pickle_files"]}

range_parameters = {
    "positive_risk_aversion": [-0.9, 0.9],
    "negative_risk_aversion": [-0.9, 0.9],
    "probability_distortion": [0.4, 1.],
    "loss_aversion": [-1.0, 0.5],
    "temp": [0.1, 0.5]
}

starting_points = \
    {
        "Havane": "2017-03-03",
        "Gladys": "2017-03-31"
    }  # "2016-12-01", "2017-03-01"

n_values_per_parameter = 10

end_point = "2017-10-01"  # today()

condition_evolution = "pool"  # Choice: "day", "beginning_vs_end", "pool"
