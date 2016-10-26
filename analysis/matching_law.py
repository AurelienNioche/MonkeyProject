from pylab import plt, np
from os import path, mkdir
from analysis import Analyst


class AnalystChild(Analyst):

    def __init__(self, database_name):

        Analyst.__init__(self, database_name=database_name)

    def import_data_for_single_session_without_errors(self, monkey, date):

        self.monkey = monkey

        session_table = \
            self.db.read_column(table_name="summary", column_name='session_table_ID', monkey=self.monkey, date=date)

        self.import_data(session_table=session_table)

        choices = list()

        quantities = {"left": [], "right": []}
        probas = {"left": [], "right": []}

        for i, error in enumerate(self.errors):

            # Consider only trials where there is no error
            if error == "None":

                choices.append(self.choices[i])
                quantities["left"].append(self.quantities["left"][i])
                quantities["right"].append(self.quantities["right"][i])
                probas["left"].append(self.probas["left"][i])
                probas["right"].append(self.probas["right"][i])

        self.choices = choices
        self.quantities = quantities
        self.probas = probas
        # print(self.probas)
        # print(self.quantities)

    def consider_congruent_trials_with_fixed_q(self, monkey, date, fig_name):

        results = dict()

        n_relevant_trials = 0

        for trial in range(len(self.choices)):

            # if self.quantities["left"][trial][0] == self.quantities["right"][trial][0]:
            #
            #     if self.probas["left"][trial] > self.probas["right"][trial]:
            #         side = ["right", "left"]
            #
            #     elif self.probas["left"][trial] < self.probas["right"][trial]:
            #         side = ["left", "right"]
            #
            #     else:
            #         # print("continue")
            #         continue
            #
            #     ratio_rate_of_reinforcement = self.probas[side[0]][trial] / \
            #                                   (self.probas[side[0]][trial] + self.probas[side[1]][trial])
            #     if ratio_rate_of_reinforcement in results:
            #         results[ratio_rate_of_reinforcement].append(int(self.choices[trial] == side[0]))
            #
            #     else:
            #
            #         results[ratio_rate_of_reinforcement] = [int(self.choices[trial] == side[0])]

            side, other_side = "left", "right"
            if self.quantities[side][trial][0] == self.quantities[other_side][trial][0]:

                n_relevant_trials += 1

                ratio_rate_of_reinforcement = self.probas[side][trial] / \
                                                  (self.probas[side][trial] + self.probas[other_side][trial])

                if ratio_rate_of_reinforcement in results:
                    results[ratio_rate_of_reinforcement].append(int(self.choices[trial] == side))
                else:

                    results[ratio_rate_of_reinforcement] = [int(self.choices[trial] == side)]

        # print("results", results)

        X = [i for i in results.keys()]
        X.sort()
        X = np.asarray(X)
        Y = np.zeros(len(X))
        y_std = np.zeros(len(X))
        for i, x in enumerate(X):
            Y[i] = np.mean(results[x])
            y_std[i] = np.std(results[x])

        # print(y_std)
        # print("results", results)
        print(results.keys())

        plt.plot(X, Y)

        plt.text(x=0.5, y=0.1, s="Trials number: {}".format(n_relevant_trials))

        plt.plot(X, Y, c='b', lw=2)
        plt.plot(X, Y + y_std, c='b', lw=.5)
        plt.plot(X, Y - y_std, c='b', lw=.5)
        plt.fill_between(X, Y + y_std, Y - y_std, color='b', alpha=.1)

        plt.xlabel("p_left / (p_left + p_right)\n", fontsize=12)
        plt.ylabel("b_left / (b_left + b_right)\n", fontsize=12)

        plt.title("Matching law? {} - {}".format(monkey, date))

        plt.xlim(min(X), max(X))
        plt.ylim(0, 1.01)
        plt.savefig(fig_name)
        plt.show()


def main():

    monkey = "Havane"
    date = "2016/08/19"

    fig_folder = "../FigSingleSession"
    if not path.exists(fig_folder): mkdir(fig_folder)
    fig_name = "{}/matching_law_{}_{}.pdf".format(fig_folder, monkey, date.replace("/", "-"))

    a = AnalystChild(database_name="../Results/results")
    a.import_data_for_single_session_without_errors(monkey=monkey, date=date)
    a.consider_congruent_trials_with_fixed_q(monkey=monkey, date=date, fig_name=fig_name)


class AnalystChild2(Analyst):

    def __init__(self, database_name):

        Analyst.__init__(self, database_name=database_name)

    def import_data_for_single_session_without_errors(self, session_table):

        self.import_data(session_table=session_table)

        choices = list()

        quantities = {"left": [], "right": []}
        probas = {"left": [], "right": []}

        for i, error in enumerate(self.errors):

            # Consider only trials where there is no error
            if error == "None":

                choices.append(self.choices[i])
                quantities["left"].append(self.quantities["left"][i])
                quantities["right"].append(self.quantities["right"][i])
                probas["left"].append(self.probas["left"][i])
                probas["right"].append(self.probas["right"][i])

        self.choices = choices
        self.quantities = quantities
        self.probas = probas

    def compute_matching_law(self, monkey, fig_name):

        results = dict()

        n_relevant_trials = 0

        self.monkey = monkey

        dates = \
            self.db.read_column(table_name="summary", column_name='date', monkey=self.monkey)

        session_tables = \
            self.db.read_column(table_name="summary", column_name='session_table_ID', monkey=self.monkey)

        for date, session_table in zip(dates, session_tables):

            # split_date = [int(i) for i in date.split("/")]
            # if (split_date[1] >= 8) * (split_date[2] > 15) or (split_date[1] > 8):
            if True:
                # print(date)

                self.import_data_for_single_session_without_errors(session_table=session_table)

                for trial in range(len(self.choices)):

                    side, other_side = "left", "right"
                    if self.quantities[side][trial][0] == self.quantities[other_side][trial][0]:

                        n_relevant_trials += 1

                        ratio_rate_of_reinforcement = self.probas[side][trial] / \
                                                          (self.probas[side][trial] + self.probas[other_side][trial])

                        if ratio_rate_of_reinforcement in results:
                            results[ratio_rate_of_reinforcement].append(int(self.choices[trial] == side))
                        else:

                            results[ratio_rate_of_reinforcement] = [int(self.choices[trial] == side)]
        self.plot_results(results, n_relevant_trials, fig_name)

    def plot_results(self, results, n_relevant_trials, fig_name):

        X = [i for i in results.keys()]
        X.sort()
        # print(X)
        X = np.asarray(X)
        Y = np.zeros(len(X))
        y_std = np.zeros(len(X))
        for i, x in enumerate(X):
            Y[i] = np.mean(results[x])
            y_std[i] = np.std(results[x])

        print(y_std)

        plt.plot(X, Y)

        plt.text(x=0.5, y=0.1, s="Trials number: {}".format(n_relevant_trials))

        plt.plot(X, Y, c='b', lw=2)
        plt.plot(X, Y + y_std, c='b', lw=.5)
        plt.plot(X, Y - y_std, c='b', lw=.5)
        plt.fill_between(X, Y + y_std, Y - y_std, color='b', alpha=.1)

        plt.xlabel("p_left / (p_left + p_right)\n", fontsize=12)
        plt.ylabel("b_left / (b_left + b_right)\n", fontsize=12)

        plt.title("Matching law? {}".format(self.monkey))

        plt.xlim(min(X), max(X))
        plt.ylim(0, 1.01)
        plt.savefig(fig_name)
        plt.show()


def main2():

    monkey = "Havane"

    fig_folder = "../FigMatchingLaw"
    if not path.exists(fig_folder): mkdir(fig_folder)
    fig_name = "{}/matching_law_{}.pdf".format(fig_folder, monkey)

    a = AnalystChild2(database_name="../Results/results")
    a.compute_matching_law(monkey, fig_name)


if __name__ == "__main__":

    main2()
