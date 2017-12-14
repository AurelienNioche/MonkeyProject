from os import makedirs
import pickle

from analysis.analysis_parameters import folders


class Backup:

    folder = folders["pickle_files"]
    makedirs(folder, exist_ok=True)

    def __init__(self, monkey, kind_of_analysis):
        self.monkey = monkey
        self.backup_file = "{}/{}_{}.p".format(self.folder, monkey, kind_of_analysis)

    def save(self, data):

        with open(self.backup_file, "wb") as f:
            pickle.dump(data, f)

    def load(self):

        try:
            with open(self.backup_file, "rb") as f:
                data = pickle.load(f)
                return data
        except FileNotFoundError:
            return
