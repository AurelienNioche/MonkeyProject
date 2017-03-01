from pylab import np, plt
from os import path
from collections import OrderedDict
from task.save import Database


class DataGetter(object):

    def __init__(self, monkey, starting_point):

        self.db = Database()
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

    def get_dates(self):

        assert self.db.table_exists("summary")
        all_dates = np.unique(self.db.read_column(table_name="summary", column_name='date', monkey=self.monkey))
        assert len(all_dates)
        dates = self.select_posterior_dates(all_dates)

        print("N dates", len(dates))

        return dates

    def get_errors_p_x0_x1_choices_from_db(self, dates):

        p = {"left": [], "right": []}
        x0 = {"left": [], "right": []}
        x1 = {"left": [], "right": []}
        error = []
        choice = []

        session = []

        for idx, date in enumerate(sorted(dates)):

            print("Dates: ", dates)
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
        print("N valid trials:", len(valid_trials))

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

        dates = self.get_dates()
        error, p, x0, x1, choice, session = self.get_errors_p_x0_x1_choices_from_db(dates)
        p, x0, x1, choice, session = self.filter_valid_trials(error, p, x0, x1, choice, session)

        return p, x0, x1, choice, session


class ProgressAnalyst(object):

    control_conditions = [
        "identical p, negative x0",
        "identical p, positive x0",
        "identical p, positive vs negative x0",
        "identical x, negative x0",
        "identical x, positive x0"
    ]

    def __init__(self, p, x0, x1, choice):

        self.p = p
        self.x0 = x0
        self.x1 = x1
        self.choice = choice
        self.trials_id = np.arange(len(self.p["left"]))

        self.dict_functions = dict()
        for key in self.control_conditions:
            self.dict_functions[key] = getattr(self, 'analyse_{}'.format(key.replace(" ", "_").replace(",", "")))

    def analyse(self, condition):

        return self.dict_functions[condition]()

    def analyse_identical_p_negative_x0(self):

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
            return hit / n

    def analyse_identical_p_positive_x0(self):

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
            return hit / n

    def analyse_identical_p_positive_vs_negative_x0(self):

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
            return hit / n

    def analyse_identical_x_positive_x0(self):

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
            return hit / n

    def analyse_identical_x_negative_x0(self):

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
            return hit / n


def main():

    starting_point = "2016-08-11"
    database_name = "results_sequential"

    for monkey in ["Havane", "Gladys"]:

        print("Analysis for {}".format(monkey))
        print()

        dg = DataGetter(monkey=monkey, starting_point=starting_point)

        p, x0, x1, choice, session = dg.run()

        progress = OrderedDict()

        for key in ProgressAnalyst.control_conditions:
            progress[key] = []

        print(progress)
        for session_id in np.unique(session):

            session_p = dict()
            session_x0 = dict()
            session_x1 = dict()

            for side in ["left", "right"]:

                session_p[side] = p[side][session == session_id]
                session_x0[side] = x0[side][session == session_id]
                session_x1[side] = x1[side][session == session_id]

            session_choice = choice[session == session_id]

            print()
            pa = ProgressAnalyst(p=session_p, x0=session_x0, x1=session_x1, choice=session_choice)
            for key in progress:
                progress[key].append(pa.analyse(key))

            print()
            print("*" * 10)
            print()

        fig = plt.figure(figsize=(25, 12))
        ax = plt.subplot(111)

        for key in progress:

            plt.plot(np.unique(session) + 1, progress[key], label=key, linewidth=2)
            plt.xticks(np.arange(len(np.unique(session))) + 1)
            plt.ylim([-0.01, 1.01])
            plt.ylabel("Success rate")
            plt.xlabel("Day")

        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

        ax.set_title(monkey)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.savefig(path.expanduser("~/Desktop/{}_progress.pdf".format(monkey)))
        plt.close()



if __name__ == "__main__":

    main()
