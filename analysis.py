# -*- coding: utf-8 -*-
import numpy as np
from save.save import Database
from collections import OrderedDict as ODict


class Analyst(object):

    def __init__(self, database_name="results"):

        self.db = Database(database_name=database_name)

        self.monkey = None

        self.choices = None
        self.errors = None
        self.probas = None
        self.quantities = None

        self.fixed_p_trials = []
        self.fixed_q_trials = []
        self.congruent_trials = []
        self.incongruent_trials = ODict()

        self.monkey_choices = ODict()
        self.monkey_choices["left"] = 0
        self.monkey_choices["right"] = 0

        self.incongruent_trials_expect = ODict()

    @staticmethod
    def str_to_list(str_element):

        to_return = str_element[1:-1]  # Remove brackets
        to_return = to_return.split(' ')  # Create list using space as delimiter
        to_return = [i for i in filter(lambda x: x != "", to_return)]  # Remove empty strings from list
        to_return = [float(i.replace(",", "")) for i in to_return]  # Convert in float, but removing coma just before

        return to_return

    def import_data(self, session_table):

        self.choices = self.db.read_column(table_name=session_table, column_name="choice")

        self.errors = \
            self.db.read_column(table_name=session_table, column_name="error")

        self.quantities = dict()

        self.probas = dict()

        for i in ["left", "right"]:

            str_quantities = self.db.read_column(table_name=session_table, column_name='{}_q'.format(i))
            self.quantities[i] = [self.str_to_list(i) for i in str_quantities]

            self.probas[i] = [float(i) for i in
                              self.db.read_column(table_name=session_table, column_name='{}_p'.format(i))]

    def analyse(self, monkey):

        print("\r")
        print("*"*100)
        print("Monkey:", monkey)
        print("*" * 100)

        self.monkey = monkey

        dates = \
            self.db.read_column(table_name="summary", column_name='date', monkey=self.monkey)

        session_tables = \
            self.db.read_column(table_name="summary", column_name='session_table_ID', monkey=self.monkey)

        print(dates, session_tables)

        for date, session_table in zip(dates, session_tables):

            self.import_data(session_table=session_table)
            self.analyse_session(date)

    def analyse_session(self, date):

        print("*****")
        print("Date:", date)

        self.monkey_choices["left"] = 0
        self.monkey_choices["right"] = 0
        self.fixed_p_trials = []
        self.fixed_q_trials = []
        self.congruent_trials = []
        self.incongruent_trials["equal_expect"] = {}
        self.incongruent_trials["equal_expect"]["risky"] = []
        self.incongruent_trials["unequal_expect"] = {}
        self.incongruent_trials["unequal_expect"]["risky>"] = []
        self.incongruent_trials["unequal_expect"]["risky<"] = []

        self.incongruent_trials_expect.clear()
        for i in [-1.25, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1.25]:

            self.incongruent_trials_expect[i] = []

        for i, error in enumerate(self.errors):

            # Consider only trials where there is no error
            if error == "None":

                self.analyse_side_bias(i)

                if self.analyse_fixed_p_trial(i):
                    pass
                elif self.analyse_fixed_q_trial(i):
                    pass
                elif self.analyse_congruent_trial(i):
                    pass
                elif self.analyse_incongruent_trial(i):
                    pass
                else:
                    pass

        self.summarise_side_bias()
        self.summarise_fixed_p_trials()
        self.summarise_fixed_q_trials()
        self.summarise_congruent_trials()
        self.summarise_incongruent_trials()

    def analyse_fixed_p_trial(self, trial):

        if self.probas["left"][trial] == self.probas["right"][trial]:

            if self.quantities["left"][trial][0] > self.quantities["right"][trial][0]:

                if self.choices[trial] == "left":

                    self.fixed_p_trials.append(1)
                else:
                    self.fixed_p_trials.append(0)

            elif self.quantities["left"][trial][0] < self.quantities["right"][trial][0]:

                if self.choices[trial] == "right":

                    self.fixed_p_trials.append(1)
                else:
                    self.fixed_p_trials.append(0)
            else:
                pass

            return 1

        else:

            return 0

    def summarise_fixed_p_trials(self):

        n = len(self.fixed_p_trials)
        if n:

            print("Fixed p/ Frequency with which the option with the highest q is chosen: {r:.2f} [{n} trials]"
                  .format(r=np.mean(self.fixed_p_trials),
                          n=len(self.fixed_p_trials)
                          ))

    def analyse_fixed_q_trial(self, trial):

        if self.quantities["left"][trial][0] == self.quantities["right"][trial][0]:

            if self.probas["left"][trial] > self.probas["right"][trial]:

                if self.choices[trial] == "left":

                    self.fixed_q_trials.append(1)
                else:
                    self.fixed_q_trials.append(0)

            elif self.probas["left"][trial] < self.probas["right"][trial]:

                if self.choices[trial] == "right":

                    self.fixed_q_trials.append(1)
                else:
                    self.fixed_q_trials.append(0)
            else:
                pass

            return 1

        else:

            return 0

    def summarise_fixed_q_trials(self):

        n = len(self.fixed_q_trials)
        if n:

            print("Fixed q / Frequency with which the option with the highest p is chosen: {r:.2f} [{n} trials]"
                  .format(r=np.mean(self.fixed_q_trials),
                          n=n
                          ))

    def analyse_congruent_trial(self, trial):

        for sides in [("left", "right"), ("right", "left")]:

            if self.quantities[sides[0]][trial][0] > self.quantities[sides[1]][trial][0] and \
                    self.probas[sides[0]][trial] > self.probas[sides[1]][trial]:

                if self.choices[trial] == sides[0]:

                    self.congruent_trials.append(1)
                else:
                    self.congruent_trials.append(0)

                return 1

        return 0

    def summarise_congruent_trials(self):
        n = len(self.congruent_trials)
        if n:

            print("Congruent: {r:.2f} [{n} trials]"
                  .format(r=np.mean(self.congruent_trials),
                          n=n
                          ))

    def analyse_incongruent_trial(self, trial):

        for sides in [("left", "right"), ("right", "left")]:

            if self.quantities[sides[0]][trial][0] > self.quantities[sides[1]][trial][0] and \
                    self.probas[sides[0]][trial] < self.probas[sides[1]][trial]:

                diff = self.quantities[sides[0]][trial][0] * self.probas[sides[0]][trial] - \
                    self.quantities[sides[1]][trial][0] * self.probas[sides[1]][trial]

                if self.choices[trial] == sides[0]:

                    self.incongruent_trials_expect[diff].append(1)
                else:
                    self.incongruent_trials_expect[diff].append(0)

                # Incongruent trial with side '0' as the risky option (higher value but weaker probability)
                if self.quantities[sides[0]][trial][0] * self.probas[sides[0]][trial] > \
                        self.quantities[sides[1]][trial][0] * self.probas[sides[1]][trial]:

                    # Expected value of side '0' is greater and it is the risky option
                    # since p of side '0' is the weakest

                    if self.choices[trial] == sides[0]:
                        # Monkey choose the risky option
                        self.incongruent_trials["unequal_expect"]["risky>"].append(1)
                    else:
                        self.incongruent_trials["unequal_expect"]["risky>"].append(0)

                elif self.quantities[sides[0]][trial][0] * self.probas[sides[0]][trial] < \
                        self.quantities[sides[1]][trial][0] * self.probas[sides[1]][trial]:
                    # Expected value of side '1' is greater and it is the safe option

                    if self.choices[trial] == sides[0]:
                        # Monkey choose the risky option while it was the option with the weaker expected value
                        self.incongruent_trials["unequal_expect"]["risky<"].append(1)
                    else:
                        self.incongruent_trials["unequal_expect"]["risky<"].append(0)
                else:
                    # Expected values are the same
                    # We know that p of side '0' is weaker
                    if self.choices[trial] == sides[0]:
                        # Monkey preferred 'risky' option
                        self.incongruent_trials["equal_expect"]["risky"].append(1)
                    else:
                        self.incongruent_trials["equal_expect"]["risky"].append(0)

                return 1

        return 0

    def summarise_incongruent_trials(self):

        n = len(self.incongruent_trials["unequal_expect"]["risky>"]) + \
            len(self.incongruent_trials["equal_expect"]["risky"]) + \
            len(self.incongruent_trials["unequal_expect"]["risky<"])

        if n:

            print("Incongruent higher expect for risky option/choose risky option: {r:.2f} [{n} trials]"
                  .format(r=np.mean(self.incongruent_trials["unequal_expect"]["risky>"]),
                          n=len(self.incongruent_trials["unequal_expect"]["risky>"])
                          ))

            print("Incongruent equal expect/choose risky option: {r:.2f} [{n} trials]"
                  .format(r=np.mean(self.incongruent_trials["equal_expect"]["risky"]),
                          n=len(self.incongruent_trials["equal_expect"]["risky"])
                          ))

            print("Incongruent higher expect for safe option/choose risky option: {r:.2f} [{n} trials]"
                  .format(r=np.mean(self.incongruent_trials["unequal_expect"]["risky<"]),
                          n=len(self.incongruent_trials["unequal_expect"]["risky<"])
                          ))

            for i in [-1.25, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1.25]:
                # print(self.incongruent_trials_expect[i])
                # print(len(self.incongruent_trials_expect[i]))
                # print(np.mean(self.incongruent_trials_expect[i]))

                print("Incongruent difference expected value for 'risky' option {}: {} [{} trials]".format(i,
                                                                     np.mean(self.incongruent_trials_expect[i]),
                                                                     len(self.incongruent_trials_expect[i])
                                                                     ))

    def analyse_side_bias(self, trial):

        choice = self.choices[trial]
        self.monkey_choices[choice] += 1

    def summarise_side_bias(self):

        print("Repartition: [left] {}; [right] {}; total: {}".format(self.monkey_choices["left"],
                                                                     self.monkey_choices["right"],
                                                                     self.monkey_choices["left"] +
                                                                     self.monkey_choices["right"]
                                                                     ))


def compute():

    analyst = Analyst(database_name="results")
    for monkey in ["Havane", "Gladys"]:  #, "Gladys":
        analyst.analyse(monkey)


if __name__ == "__main__":

    compute()
