from pylab import np

from utils.utils import log


class DataSorter:

    name = "DataSorter"

    def __init__(self, data, sort_type, pool_size=10):

        self.data = data
        self.n_dates = 0
        self.sort_type = sort_type
        self.pool_size = pool_size  # Will be needed in case of arbitrary trials pooling

        self.sorted_data = []

    def run(self):

        log("Sort data...", self.name)

        if self.sort_type == "day":
            self.sort_data_per_day()

        elif self.sort_type == "beginning_vs_end":
            self.sort_data_beginning_vs_end()

        elif self.sort_type == "pool":
            self.sort_data_pool()

        else:
            raise Exception("Sort type not understood.")

        log("Done.", self.name)

        return self.sorted_data

    def sort_data_beginning_vs_end(self):

        # A list of two dictionaries that will contain data :
        # - one for the beginning of each session,
        # - one for the end.

        self.sorted_data = [
            {k: [] if k == "choice" else {side: [] for side in ["left", "right"]}
                for k in ["p", "x0", "choice"]} for i in range(2)]

        for i, session_id in enumerate(np.unique(self.data["session"])):

            idx = self.data["session"] == session_id
            part = len(self.data["choice"][idx]) // 2

            for item in ["p", "x0"]:
                for side in ["left", "right"]:
                    data = list(self.data[item][side][idx])
                    self.sorted_data[0][item][side] += data[:part]
                    self.sorted_data[1][item][side] += data[part:]

            data = list(self.data["choice"][idx])
            self.sorted_data[0]["choice"] += data[:part]
            self.sorted_data[1]["choice"] += data[part:]
            self.n_dates += 1

    def sort_data_pool(self):

        self.n_dates = len(np.unique(self.data["session"]))

        n_groups = self.n_dates // self.pool_size

        self.prepare_results_container_for_n_groups(n_groups)

        for i, (session_id, date) in enumerate(zip(np.unique(self.data["session"]), np.unique(self.data["date"]))):

            # group to which this particular session will belong to
            group = i // self.pool_size

            if group >= n_groups:
                log("I will ignore the {} last sessions for having pool of equal size.".format(self.n_dates - i),
                    self.name)
                break

            idx = self.data["session"] == session_id

            # Sort the date of this particular session in the appropriate group
            for item in ["p", "x0"]:
                for side in ["left", "right"]:
                    self.sorted_data[group][item][side] += list(self.data[item][side][idx])

            self.sorted_data[group]["choice"] += list(self.data["choice"][idx])
            self.sorted_data[group]["dates"] += list(self.data["date"][idx])

    def sort_data_per_day(self):

        for i, session_id in enumerate(np.unique(self.data["session"])):

            self.sorted_data.append({})

            idx = self.data["session"] == session_id

            for item in ["p", "x0"]:

                self.sorted_data[i][item] = dict()

                for side in ["left", "right"]:
                    self.sorted_data[i][item][side] = self.data[item][side][idx]

            self.sorted_data[i]["choice"] = self.data["choice"][idx]
            self.n_dates += 1

    def prepare_results_container_for_n_groups(self, n_groups):

        # A list of dictionaries that will contain data, one for each pool.
        self.sorted_data = []

        for i in range(n_groups):

            data = {}

            for key in ("choice", "dates"):
                data[key] = []

            for key in ("p", "x0"):
                data[key] = {side: [] for side in ["left", "right"]}

            self.sorted_data.append(data)


def sort_data(data, sort_type, pool_size=10):

    data_sorter = DataSorter(data, sort_type, pool_size)
    return data_sorter.run()
