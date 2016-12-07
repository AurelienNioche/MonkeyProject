import numpy as np
from os import path
from task.save import Database


class DataGetter(object):

    def __init__(self, database_folder, database_name, monkey, starting_point):

        self.db = Database(database_folder=database_folder, database_name=database_name)
        self.monkey = monkey
        self.starting_point = starting_point

    def select_posterior_dates(self, dates_list):

        starting_point = [int(i) for i in self.starting_point.split("-")]

        new_dates = []
        for str_date in dates_list:
            date = [int(i) for i in str_date.split("-")]
            if date[0] > starting_point[0]:

                new_dates.append(str_date)
            elif date[0] == starting_point[0]:
                if date[1] > starting_point[1]:
                    new_dates.append(str_date)
                elif date[1] == starting_point[1]:
                    if date[2] >= starting_point[2]:
                        new_dates.append(str_date)
        return new_dates

    def get_errors_p_x0_x1_choices_from_db(self, dates):

        p = {"left": [], "right": []}
        x0 = {"left": [], "right": []}
        x1 = {"left": [], "right": []}
        error = []
        choice = []

        for date in dates:

            session_table = \
                self.db.read_column(table_name="summary", column_name='session_table',
                                    monkey=self.monkey, date=date)

            if type(session_table) == list:
                session_table = session_table[-1]

            error += \
                self.db.read_column(table_name=session_table, column_name="error")

            choice += \
                self.db.read_column(table_name=session_table, column_name="choice")

            for side in ["left", "right"]:

                p[side] += \
                    [float(i) for i in self.db.read_column(table_name=session_table, column_name='{}_p'.format(side))]
                x0[side] += \
                    [int(i) for i in self.db.read_column(table_name=session_table, column_name='{}_x0'.format(side))]
                x1[side] += \
                    [int(i) for i in self.db.read_column(table_name=session_table, column_name='{}_x1'.format(side))]

        return error, p, x0, x1, choice

    def get_dates(self):
        assert self.db.table_exists("summary")
        all_dates = np.unique(self.db.read_column(table_name="summary", column_name='date', monkey=self.monkey))
        assert len(all_dates)
        dates = self.select_posterior_dates(all_dates)

        print("N dates", len(dates))

        return dates

    @staticmethod
    def filter_valid_trials(error, p, x0, x1, choice):

        new_p = {"left": [], "right": []}
        new_x0 = {"left": [], "right": []}
        new_x1 = {"left": [], "right": []}
        new_choice = []

        valid_trials = np.where(np.asarray(error) == "None")[0]
        print("N valid trials:", len(valid_trials))

        for valid_idx in valid_trials:

            new_choice.append(choice[valid_idx])

            for side in ["left", "right"]:

                new_p[side].append(p[side][valid_idx])
                new_x0[side].append(x0[side][valid_idx])
                new_x1[side].append(x1[side][valid_idx])

        return new_p, new_x0, new_x1, new_choice

    def run(self):

        dates = self.get_dates()
        error, p, x0, x1, choice = self.get_errors_p_x0_x1_choices_from_db(dates)
        p, x0, x1, choice = self.filter_valid_trials(error, p, x0, x1, choice)

        return p, x0, x1, choice


class ProgressAnalyst(object):

    def __init__(self, p, x0, x1, choice):

        self.p = p
        self.x0 = x0
        self.x1 = x1
        self.choice = choice
        self.trials_id = np.arange(len(self.p["left"]))

    def run(self):

        self.analyse_p_identical_x0_negative()
        self.analyse_p_identical_x0_positive()
        self.analyse_p_identical_x0_positive_xs_negative()
        self.analyse_identical_negative_x0()
        self.analyse_identical_positive_x0()

    def analyse_p_identical_x0_negative(self):

        n = 0
        hit = 0

        assert len(self.choice) == len(self.trials_id)

        for i in self.trials_id:

            if self.p["left"][i] == self.p["right"][i] and self.x1["left"][i] == self.x1["right"][i] \
                    and self.x0["left"][i] < 0 and self.x0["right"][i] < 0:

                n += 1

                if (self.choice[i] == "left") == (self.x0["left"][i] > self.x0["right"][i]):

                    hit += 1
        if n:

            print("Success rate with identical p, negative x0: {:.2f}".format(hit / n))

    def analyse_p_identical_x0_positive(self):

        n = 0
        hit = 0

        assert len(self.choice) == len(self.trials_id)

        for i in self.trials_id:

            if self.p["left"][i] == self.p["right"][i] and self.x1["left"][i] == self.x1["right"][i] \
                    and self.x0["left"][i] > 0 and self.x0["right"][i] > 0:

                n += 1

                if (self.choice[i] == "left") == (self.x0["left"][i] > self.x0["right"][i]):

                    hit += 1
        if n:
            print("Success rate with identical p, positive x0: {:.2f}".format(hit / n))

    def analyse_p_identical_x0_positive_xs_negative(self):

        n = 0
        hit = 0

        assert len(self.choice) == len(self.trials_id)

        for i in self.trials_id:

            if self.p["left"][i] == self.p["right"][i] and self.x1["left"][i] == self.x1["right"][i] \
                    and (self.x0["left"][i] > 0 > self.x0["right"][i] or
                         self.x0["left"][i] < 0 < self.x0["right"][i]):

                n += 1

                if (self.choice[i] == "left") == (self.x0["left"][i] > self.x0["right"][i]):

                    hit += 1

        if n:

            print("Success rate with identical p, positive vs negative x0: {:.2f}".format(hit / n))

    def analyse_identical_positive_x0(self):

        n = 0
        hit = 0

        for i in self.trials_id:

            if self.x0["left"][i] == self.x0["right"][i] and self.x1["left"][i] == self.x1["right"][i] and \
                    self.x0["left"][i] > 0:

                n += 1

                if (self.choice[i] == "left") == (self.p["left"][i] > self.p["right"][i]):
                    hit += 1
        if n:
            print("Success rate with identical x, positive x0: {:.2f}".format(hit / n))

    def analyse_identical_negative_x0(self):

        n = 0
        hit = 0

        for i in self.trials_id:

            if self.x0["left"][i] == self.x0["right"][i] and self.x1["left"][i] == self.x1["right"][i] and \
                    self.x0["left"][i] < 0:

                n += 1

                if (self.choice[i] == "left") == (self.p["left"][i] < self.p["right"][i]):
                    hit += 1

        if n:
            print("Success rate with identical x, negative x0: {:.2f}".format(hit / n))


def main():

    starting_point = "2016-08-11"
    database_folder = "../../results"
    database_name = "results_sequential"

    assert path.exists("{}/{}.db".format(database_folder, database_name))

    for monkey in ["Havane", "Gladys"]:

        print("Analysis for {}".format(monkey))
        print()

        dg = DataGetter(database_folder=database_folder, database_name=database_name,
                        monkey=monkey, starting_point=starting_point)

        p, x0, x1, choice = dg.run()

        print()
        pa = ProgressAnalyst(p=p, x0=x0, x1=x1, choice=choice)
        pa.run()

        print()
        print("*" * 10)
        print()


if __name__ == "__main__":

    main()
