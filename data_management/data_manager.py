import numpy as np

from data_management.database import Database
from utils.utils import log, today


class DataManager(object):

    def __init__(self, monkey, starting_point="2016-12-01", end_point=today()):

        self.db = Database()
        self.monkey = monkey
        self.starting_point = starting_point
        self.end_point = end_point

    def select_relevant_dates(self, dates_list):

        starting_point = [int(i) for i in self.starting_point.split("-")]
        end_point = [int(i) for i in self.end_point.split("-")]

        relevant_dates = []
        for str_date in dates_list:

            date = [int(i) for i in str_date.split("-")]

            if end_point[0] > date[0] > starting_point[0]:

                relevant_dates.append(str_date)

            elif date[0] == starting_point[0] and date[0] == end_point[0]:

                if end_point[1] > date[1] > starting_point[1]:
                    relevant_dates.append(str_date)

                elif date[1] == starting_point[1] and date[1] == end_point[1]:

                    if end_point[2] >= date[2] >= starting_point[2]:
                        relevant_dates.append(str_date)

                elif date[1] == starting_point[1]:

                    if date[2] >= starting_point[2]:
                        relevant_dates.append(str_date)

                elif date[1] == end_point[1]:

                    if end_point[2] >= date[2]:
                        relevant_dates.append(str_date)

            elif date[0] == starting_point[0]:

                if end_point[1] > date[1] > starting_point[1]:
                    relevant_dates.append(str_date)

                elif date[1] == starting_point[1] or date[1] == end_point[1]:

                    if end_point[2] >= date[2] >= starting_point[2]:
                        relevant_dates.append(str_date)

            elif date[0] == end_point[0]:

                if end_point[1] > date[1]:
                    relevant_dates.append(str_date)

                elif date[1] == end_point[1]:

                    if end_point[2] >= date[2]:
                        relevant_dates.append(str_date)

        return relevant_dates

    def get_dates(self):

        assert self.db.table_exists("summary")
        all_dates = np.unique(self.db.read_column(table_name="summary", column_name='date', monkey=self.monkey))
        assert len(all_dates)
        dates = self.select_relevant_dates(all_dates)

        log("[DataManager] N dates: {}.".format(len(dates)))

        return dates

    def get_errors_p_x0_x1_choices_from_db(self, dates):

        p = {"left": [], "right": []}
        x0 = {"left": [], "right": []}
        x1 = {"left": [], "right": []}
        error = []
        choice = []

        session = []

        for idx, date in enumerate(sorted(dates)):

            # print("Dates: ", dates)
            session_table = \
                self.db.read_column(table_name="summary", column_name='session_table',
                                    monkey=self.monkey, date=date)

            if type(session_table) == list:
                session_table = session_table[-1]

            error_session = self.db.read_column(table_name=session_table, column_name="error")
            choice_session = self.db.read_column(table_name=session_table, column_name="choice")

            error += error_session

            choice += choice_session

            session += [idx, ] * len(error_session)

            for side in ["left", "right"]:

                p[side] += \
                    [float(i) for i in self.db.read_column(table_name=session_table, column_name='{}_p'.format(side))]
                x0[side] += \
                    [int(i) for i in self.db.read_column(table_name=session_table, column_name='{}_x0'.format(side))]
                x1[side] += \
                    [int(i) for i in self.db.read_column(table_name=session_table, column_name='{}_x1'.format(side))]

        return error, p, x0, x1, choice, session

    @staticmethod
    def filter_valid_trials(error, p, x0, x1, choice, session):

        new_p = {"left": [], "right": []}
        new_x0 = {"left": [], "right": []}
        new_x1 = {"left": [], "right": []}
        new_choice = []
        new_session = []

        valid_trials = np.where(np.asarray(error) == "None")[0]
        log("[DataManager] N valid trials: {}.".format(len(valid_trials)))

        for valid_idx in valid_trials:

            new_session.append(session[valid_idx])

            new_choice.append(choice[valid_idx])

            for side in ["left", "right"]:

                new_p[side].append(p[side][valid_idx])
                new_x0[side].append(x0[side][valid_idx])
                new_x1[side].append(x1[side][valid_idx])

        for side in ["left", "right"]:
            new_p[side] = np.asarray(new_p[side])
            new_x0[side] = np.asarray(new_x0[side])
            new_x1[side] = np.asarray(new_x1[side])

        new_choice = np.asarray(new_choice)
        new_session = np.asarray(new_session)
        return new_p, new_x0, new_x1, new_choice, new_session

    def run(self):

        log("[DataManager] Import data for {}.".format(self.monkey))

        dates = self.get_dates()
        error, p, x0, x1, choice, session = self.get_errors_p_x0_x1_choices_from_db(dates)
        p, x0, x1, choice, session = self.filter_valid_trials(error, p, x0, x1, choice, session)

        log("[DataManager] Done!")

        return {"p": p, "x0": x0, "x1": x1, "choice": choice, "session": session}


def import_data(monkey, starting_point="2016-12-01", end_point=today()):

    d = DataManager(monkey=monkey, starting_point=starting_point, end_point=end_point)
    return d.run()
