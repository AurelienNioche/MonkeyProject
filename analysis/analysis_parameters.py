from os import path
from utils.utils import today

folders = {
    "figures": path.expanduser("~/Desktop/monkey_figures"),
    "results": path.expanduser("~/Desktop/monkey_results_modelling"),
    "npy_files": path.expanduser("~/Desktop/monkey_npy_files")
}

starting_point = "2017-03-01"
end_point = today()
