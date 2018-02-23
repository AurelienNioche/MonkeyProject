from os import makedirs
import pickle

"""
module for loading data from pickle file
"""


class Backup:

    def __init__(self, monkey, kind_of_analysis, folder):

        makedirs(folder, exist_ok=True)

        self.monkey = monkey
        self.backup_file = "{}/{}_{}.p".format(folder, monkey, kind_of_analysis)

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
