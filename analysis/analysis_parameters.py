from os import path
from utils.utils import today

folders = {
    "figures": path.expanduser("~/Desktop/MonkeyResults{}/figures".format(today())),
    "results": path.expanduser("~/Desktop/MonkeyResults{}/modelling".format(today())),
    "npy_files": path.expanduser("~/Desktop/MonkeyResults{}/monkey_npy_files".format(today()))
}

range_parameters = {
    "positive_risk_aversion": [-0.9, 0.9],
    "negative_risk_aversion": [-0.9, 0.9],
    "probability_distortion": [0.4, 1.],
    "loss_aversion": [-1.0, 0.5],
    "temp": [0.1, 0.5]
}

n_values_per_parameter = 10

starting_point = "2016-12-01"  # "2017-03-01
end_point = today()

condition_evolution = "pool"  # Choice: "day", "beginning_vs_end", "pool"
