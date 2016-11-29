from pylab import plt, np
from task.save import Database
from os import path, mkdir
from multiprocessing import Pool, cpu_count
from itertools import product
from scipy.stats import binom
from scipy.optimize import curve_fit
import ternary


def str_to_list(str_element):

    to_return = str_element[1:-1]  # Remove brackets
    to_return = to_return.split(' ')  # Create list using space as delimiter
    to_return = [i for i in filter(lambda x: x != "", to_return)]  # Remove empty strings from list
    to_return = [float(i.replace(",", "")) for i in
                 to_return]  # Convert in float, but removing coma just before

    return to_return


def select_posterior_dates(dates_list, starting_point):

    starting_point = [int(i) for i in starting_point.split("-")]

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


class ArchetypeFinder(object):

    def __init__(self, database_folder, database_name, starting_point):

        self.db = Database(database_folder=database_folder, database_name=database_name)
        self.monkey_reference = "Havane"
        self.starting_point = starting_point

    @staticmethod
    def expected_value(lottery):

        return lottery[0] * lottery[1]

    @staticmethod
    def get_incongruent_lotteries(lotteries):

        incongruent_lotteries = []
        for l0, l1 in lotteries:

            if l0[0] < l1[0] and l0[1] > l1[1]:

                incongruent_lotteries.append((l0, l1))

            elif l0[0] > l1[0] and l0[1] < l1[1]:

                # Order is reversed here for having risky lottery in front
                incongruent_lotteries.append((l1, l0))

        n_incongruent_lotteries = len(incongruent_lotteries)
        print("N incongruent lotteries:", n_incongruent_lotteries)

        return incongruent_lotteries

    @staticmethod
    def select_unique_lotteries(errors, probas, quantities):

        lotteries = []

        for t in range(len(errors)):

            if errors[t] == "None":
                lottery = (
                    (probas["left"][t], quantities["left"][t]),
                    (probas["right"][t], quantities["right"][t])

                )

                if lottery not in lotteries and lottery[::-1] not in lotteries:
                    lotteries.append(lottery)

        return lotteries

    def run(self):

        all_dates = self.db.read_column(table_name="summary", column_name='date', monkey=self.monkey_reference)
        dates = select_posterior_dates(all_dates, self.starting_point)
        print("Dates", dates)
        print("N dates", len(dates))

        errors, probas, quantities = self.get_errors_probas_and_quantities_from_db(dates)

        lotteries = self.select_unique_lotteries(errors, probas, quantities)

        print("N unique couple of lotteries:", len(lotteries))

        incongruent_lotteries_in_arbitrary_order = self.get_incongruent_lotteries(lotteries)

        incongruent_lotteries = \
            self.class_lotteries_according_to_difference_in_expected_value(incongruent_lotteries_in_arbitrary_order)

        return incongruent_lotteries

    def get_errors_probas_and_quantities_from_db(self, dates):

        probas = {"left": [], "right": []}
        quantities = {"left": [], "right": []}
        errors = []
        for date in dates:

            session_table = \
                self.db.read_column(table_name="summary", column_name='session_table',
                                    monkey=self.monkey_reference, date=date)

            errors += \
                self.db.read_column(table_name=session_table, column_name="error")

            for side in ["left", "right"]:

                probas[side] += \
                    [float(i) for i in self.db.read_column(table_name=session_table, column_name='{}_p'.format(side))]
                quantities[side] += \
                    [int(i) for i in self.db.read_column(table_name=session_table, column_name='{}_x0'.format(side))]

        return errors, probas, quantities

    def class_lotteries_according_to_difference_in_expected_value(self, lotteries_list):

        diff_exp_values = np.zeros(len(lotteries_list))

        i = 0
        for l0, l1 in lotteries_list:

            diff_exp_values[i] = self.expected_value(l0) - self.expected_value(l1)
            i += 1

        lotteries = np.asarray(lotteries_list)
        lotteries_with_new_order = np.zeros(lotteries.shape)

        sorted_diff_exp_values = np.sort(np.unique(diff_exp_values))
        print('Sorted differences in expected value', sorted_diff_exp_values)

        i = 0
        for v in sorted_diff_exp_values:

            idx_list = np.where(diff_exp_values == v)[0]

            for idx in idx_list:

                lotteries_with_new_order[i, :, :] = lotteries[idx, :, :]
                i += 1

        return lotteries_with_new_order


class Model(object):

    reward_max = 4

    def __init__(self, r, tau,  alpha):

        self.r = r
        self.tau = tau
        self.alpha = alpha

    def softmax(self, x1, x2):

        """Compute softmax values for each sets of scores in x."""
        # print("x", x)
        # return np.exp(x / tau) / np.sum(np.exp(x / tau), axis=0)
        return 1/(1+np.exp(-(1/self.tau)*(x1-x2)))

    def u(self, x):

        """Compute utility for a single output considering a parameter of risk-aversion"""
        if x > 0:
            return (x/self.reward_max) ** (1-self.r)
        elif x == 0:
            return 0
        else:
            raise Exception("Reward can not be negative")

    def U(self, L):

        # print("L", L)
        p, v = L[0], L[1]
        y = self.w(p) * self.u(v)

        # y = 0
        # for p, v in L:
        #     print(p, v)
        #
        #     y += p * cls.u(v, r)
        return y

    def w(self, p):

        return np.exp(-(-np.log(p))**self.alpha)

    def get_p(self, lottery_0, lottery_1):

        # print(lottery_0, lottery_1)
        U0, U1 = self.U(lottery_0), self.U(lottery_1)

        p_choose_U0 = self.softmax(U0, U1)

        return p_choose_U0


class ModelRunner(object):

    def __init__(self):

        self.n_values_per_parameter = 50
        self.possible_r_values = np.linspace(-1., 1., self.n_values_per_parameter)
        self.possible_tau_values = np.linspace(0.005, 1., self.n_values_per_parameter)
        self.possible_alpha_values = np.linspace(0., 1., self.n_values_per_parameter)

        self.n_parameters_vectors = len(self.possible_alpha_values) \
                                    * len(self.possible_tau_values) \
                                    * len(self.possible_r_values)

        self.parameters = np.zeros((self.n_parameters_vectors, 3))

        self.pool = Pool(processes=cpu_count())

    @staticmethod
    def compute(param):

        ps = []

        r, tau, alpha = param[0], param[1], param[2]
        lotteries = param[3]
        for l1, l2 in lotteries:

            model = Model(r=r, tau=tau, alpha=alpha)

            p = model.get_p(l1, l2)

            ps.append(p)

        return ps

    def prepare_run(self, lotteries):

        param_for_workers = []

        i = 0
        for r, tau, alpha in product(self.possible_r_values, self.possible_tau_values, self.possible_alpha_values):
            self.parameters[i] = r, tau, alpha
            param_for_workers.append([r, tau, alpha, lotteries])
            i += 1

        return param_for_workers

    def run(self, lotteries):

        param_for_workers = self.prepare_run(lotteries)

        p_values = self.pool.map(self.compute, param_for_workers)

        return self.parameters, p_values


class DataGetter(object):

    def __init__(self, database_folder, database_name, starting_point, monkey):

        self.db = Database(database_folder=database_folder, database_name=database_name)
        self.monkey = monkey
        self.starting_point = starting_point

    def get_errors_choices_probas_and_quantities(self, dates):

        probas = {"left": [], "right": []}
        quantities = {"left": [], "right": []}
        errors = []
        choices = []
        for date in dates:

            session_table = \
                self.db.read_column(table_name="summary", column_name='session_table',
                                    monkey=self.monkey, date=date)

            # If multiple tables for the same day and the same monkey, take only the last one!
            if type(session_table) == list:
                session_table = session_table[-1]

            errors += \
                self.db.read_column(table_name=session_table, column_name="error")

            choices += \
                [i == "left" for i in self.db.read_column(table_name=session_table, column_name="choice")]

            for side in ["left", "right"]:
                probas[side] += \
                    [float(i) for i in self.db.read_column(table_name=session_table, column_name='{}_p'.format(side))]

                quantities[side] += \
                    [int(i) for i in self.db.read_column(table_name=session_table, column_name='{}_x0'.format(side))]

        choices = np.asarray(choices)

        return errors, choices, probas, quantities

    def get_n_and_k_per_lotteries(self, lotteries):

        dates = self.db.read_column(table_name="summary", column_name='date', monkey=self.monkey)

        dates = select_posterior_dates(dates, self.starting_point)

        print("Dates", dates)
        print("N dates", len(dates))

        n_per_lotteries = np.zeros(len(lotteries))
        k_per_lotteries = np.zeros(len(lotteries))

        errors, choices, probas, quantities = self.get_errors_choices_probas_and_quantities(dates)

        print("N trials (errors included)", len(choices))

        valid_trials = np.where(np.asarray(errors) == "None")[0]
        print("N valid trials:", len(valid_trials))

        for i in valid_trials:
            lottery = np.array([
                [probas["left"][i], quantities["left"][i]],
                [probas["right"][i], quantities["right"][i]]
            ])

            for idx, ex_lottery in enumerate(lotteries):

                if ex_lottery[0][0] == lottery[0][0] and \
                        ex_lottery[0][1] == lottery[0][1] and \
                        ex_lottery[1][0] == lottery[1][0] and \
                        ex_lottery[1][1] == lottery[1][1]:

                    n_per_lotteries[idx] += 1
                    k_per_lotteries[idx] += choices[i]
                    break
                elif ex_lottery[0][0] == lottery[1][0] and \
                        ex_lottery[0][1] == lottery[1][1] and \
                        ex_lottery[1][0] == lottery[0][0] and \
                        ex_lottery[1][1] == lottery[0][1]:

                    n_per_lotteries[idx] += 1
                    k_per_lotteries[idx] += 1 - choices[i]
                    break

        print("N per lotteries: ", n_per_lotteries)
        print("K per lotteries:", k_per_lotteries)

        return n_per_lotteries, k_per_lotteries


class MLEComputer(object):

    def __init__(self, model_parameters, model_p_values, exp_n_values, exp_k_values):

        self.model_parameters = model_parameters
        self.model_p_values = model_p_values
        self.exp_n_values = exp_n_values
        self.exp_k_values = exp_k_values

    def __call__(self, m):

        log_likelihood_sum = 0

        for i in range(len(self.exp_n_values)):
            k, n, p = self.exp_k_values[i], self.exp_n_values[i], self.model_p_values[m, i]

            likelihood = binom.pmf(k=k, n=n, p=p)
            log_likelihood = np.log(likelihood)
            log_likelihood_sum += log_likelihood

        return log_likelihood_sum


class Fit(object):

    def __init__(self, model_parameters, model_p_values, exp_n_values, exp_k_values):

        self.model_parameters = model_parameters
        self.model_p_values = model_p_values
        self.exp_n_values = exp_n_values
        self.exp_k_values = exp_k_values
        self.pool = Pool(processes=cpu_count())

    def run(self, method):

        if method == "LSE":

            output = self.fit_with_LSE()

        elif method == "MLE":

            output = self.fit_with_MLE()

        else:
            raise Exception("Method {} is not defined for fitting data...".format(method))

        return output

    def fit_with_LSE(self):

        print("Doing LSE fit...")

        sse = np.zeros(len(self.model_parameters))

        exp_mean = self.exp_k_values/self.exp_n_values

        for m in range(len(self.model_parameters)):

            sse[m] = np.sum(np.power(self.model_p_values[m] - exp_mean[:], 2))

        print("Done.")

        return sse

    def fit_with_MLE(self):

        print("Doing MLE fit...")

        lls = self.pool.map(
            MLEComputer(
                self.model_parameters, self.model_p_values,
                self.exp_n_values, self.exp_k_values
            ),
            np.arange(len(self.model_parameters))
        )
        lls = np.asarray(lls)

        print("Done")

        return lls


class Analysis(object):

    def __init__(self, lse_fit, mle_fit, model_parameters, monkey, figure_folder, n_trials):

        self.lse_fit = lse_fit
        self.mle_fit = mle_fit
        self.model_parameters = model_parameters
        self.monkey = monkey
        self.n_trials = n_trials
        self.parameters_name = ["r", "tau", "alpha"]
        self.fig_folder = figure_folder

    def run(self):

        self.create_folder()

        self.analyse_lse_fit()
        print()
        self.analyse_mle_fit()
        print()

    def create_folder(self):

        if not path.exists(self.fig_folder):
            mkdir(self.fig_folder)

    def analyse_lse_fit(self):

        # ------------------ #
        # Analysis in console
        # ------------------ #

        self.lse_basic_analysis()

        # ------------------ #
        # One plot per parameter
        # ------------------ #

        self.lse_plot_error_according_to_parameter_values()

        # ------------------ #
        # Phase diagram
        # ------------------ #

        self.lse_plot_phase_diagram()

    def lse_basic_analysis(self, force=False):

        file_name = "{}/{}_{}_basic_analysis.txt".format(self.fig_folder, "lse", self.monkey)

        if path.exists(file_name) and not force:

            pass

        else:
            file = open(file_name, mode="w")

            txt = ""
            txt += "Least square estimation for {}".format(self.monkey)
            txt += "\n[r, tau, alpha], from the best to the worst:"

            ordered_idx_fit = np.argsort(self.lse_fit.copy())
            txt += "\n{}".format(self.model_parameters[ordered_idx_fit])

            file.write(txt)

    def lse_plot_error_according_to_parameter_values(self, force=False):

        for param in range(3):

            fig_name = "{}/{}_{}_{}.pdf".format(self.fig_folder, "lse", self.monkey, self.parameters_name[param])

            if path.exists(fig_name) and not force:

                pass

            else:

                x = np.unique(self.model_parameters[:, param])
                y = []
                y_std = []

                for value in x:
                    data = self.lse_fit[self.model_parameters[:, param] == value]

                    y.append(np.mean(data))
                    y_std.append(np.std(data))

                y = np.asarray(y)

                y_std = np.asarray(y_std)

                self.plot(x=x,
                          y=y,
                          y_std=y_std,
                          x_label=self.parameters_name[param],
                          y_label="Mean of squared errors sum",
                          monkey=self.monkey,
                          parameter=self.parameters_name[param],
                          fig_name=fig_name)

    def lse_plot_phase_diagram(self, force=False, inv_colors=False):

        if inv_colors:

            fig_name = "{}/{}_lse_inv_colors.pdf".format(self.fig_folder, self.monkey)

        else:
            fig_name = "{}/{}_lse.pdf".format(self.fig_folder, self.monkey)

        if path.exists(fig_name) and force is False:

            pass

        else:

            # Get the list of tested parameters
            r_values = np.unique(self.model_parameters[:, 0])
            tau_values = np.unique(self.model_parameters[:, 1])
            alpha_values = np.unique(self.model_parameters[:, 2])

            assert len(r_values) == len(tau_values) and len(tau_values) == len(alpha_values), \
                "The same number of data points for each parameter is required."

            # Scale is the number of data points per parameter
            scale = len(np.unique(self.model_parameters[:, 0])) - 1

            # Format data (dict with parameters tuple for key values and errors as values)
            v_dic = dict()

            i = 0
            for r, tau, alpha in self.model_parameters:
                v_dic[(r, tau, alpha)] = self.lse_fit[i]
                i += 1

            # Create points
            data = dict()
            for (i, j, k) in ternary.helpers.simplex_iterator(scale):
                data[(i, j, k)] = v_dic[(r_values[i], tau_values[j], alpha_values[k])]

            # Create figure
            figure, tax = ternary.figure(scale=scale)

            # Remove border
            fig_gca = figure.gca()
            fig_gca.set_frame_on(False)

            tax.boundary(linewidth=2.0)

            if inv_colors:
                color_map = "viridis"
            else:
                color_map = "viridis_r"
            tax.heatmap(data, scale=scale, style="triangular", cmap=color_map)
            # tax.gridlines(color="blue", multiple=5)
            tax.set_title("{} - Mean of squared error sums - 30 pairs of lotteries - {} trials\n"
                          .format(self.monkey, self.n_trials), fontsize=13)

            font_size = 20
            offset = 0.15

            tax.bottom_axis_label(r"$r$", fontsize=font_size, offset=- offset / 4)
            tax.right_axis_label(r"$\tau$", fontsize=font_size, offset=offset)
            tax.left_axis_label(r"$\alpha$", fontsize=font_size, offset=offset)

            order = ["b", "r", "l"]  # Remain that order is bottom, right, left

            for i in range(3):
                ticks = ["%.2f" % i for i in
                         np.linspace(min(self.model_parameters[:, i]),
                                     max(self.model_parameters[:, i]),
                                     5)]

                offset = 0.028
                if i == 0:
                    offset /= 1.5
                tax.ticks(ticks=ticks, axis=order[i], linewidth=1, offset=offset)

            tax.clear_matplotlib_ticks()
            tax._redraw_labels()  # Bug in saving fig otherwise on Mac OSX

            plt.savefig(fig_name)
            plt.close()

    def analyse_mle_fit(self):

        # ------------------ #
        # Analysis in console
        # ------------------ #

        self.mle_basic_analysis()

        # ------------------ #
        # One plot per parameter
        # ------------------ #

        self.mle_plot_error_according_to_parameter_value()

        # ------------------ #
        # Phase diagram
        # ------------------ #

        self.mle_plot_phase_diagram()

    def mle_basic_analysis(self, force=False):

        file_name = "{}/{}_{}_basic_analysis.txt".format(self.fig_folder, "mle", self.monkey)

        if path.exists(file_name) and not force:

            pass

        else:
            file = open(file_name, mode="w")

            txt = ""
            txt += "Maximum likelihood estimation for {}".format(self.monkey)
            txt += "\n[r, tau, alpha], from the best to the worst:"

            ordered_idx_fit = np.argsort(self.mle_fit.copy())[::-1]
            txt += "\n{}".format(self.model_parameters[ordered_idx_fit])

            file.write(txt)

    def mle_plot_error_according_to_parameter_value(self, force=False):

        # To avoid to have - infinite in data, cancel log transformation

        likelihood = np.exp(self.mle_fit)

        # print()
        # print(self.mle_fit)
        # print('*****')
        # print(likelihood)

        for param in range(3):

            fig_name = "{}/{}_{}_{}.pdf".format(self.fig_folder, "mle", self.monkey, self.parameters_name[param])

            if path.exists(fig_name) and not force:

                pass

            else:

                x = np.unique(self.model_parameters[:, param])
                y = []
                y_std = []

                for value in x:
                    data = likelihood[self.model_parameters[:, param] == value]

                    y.append(np.mean(data))
                    y_std.append(np.std(data))

                y = np.asarray(y)

                y_std = np.asarray(y_std)

                self.plot(x=x,
                          y=y,
                          y_std=y_std,
                          x_label=self.parameters_name[param],
                          y_label="Mean of likelihood",
                          monkey=self.monkey,
                          parameter=self.parameters_name[param],
                          fig_name=fig_name)

    def mle_plot_phase_diagram(self, force=False):

        likelihood = np.exp(self.mle_fit)

        fig_name = "{}/{}_mle.pdf".format(self.fig_folder, self.monkey)

        if path.exists(fig_name) and not force:

            pass

        else:

            # Get the list of tested parameters
            r_values = np.unique(self.model_parameters[:, 0])
            tau_values = np.unique(self.model_parameters[:, 1])
            alpha_values = np.unique(self.model_parameters[:, 2])

            assert len(r_values) == len(tau_values) and len(tau_values) == len(alpha_values), \
                "The same number of data points for each parameter is required."

            # Scale is the number of data points per parameter
            scale = len(np.unique(self.model_parameters[:, 0])) - 1

            # Format data (dict with parameters tuple for key values and errors as values)
            v_dic = dict()

            i = 0
            for r, tau, alpha in self.model_parameters:
                v_dic[(r, tau, alpha)] = likelihood[i]
                i += 1

            # Create points
            data = dict()
            for (i, j, k) in ternary.helpers.simplex_iterator(scale):
                data[(i, j, k)] = v_dic[(r_values[i], tau_values[j], alpha_values[k])]

            # Create figure
            figure, tax = ternary.figure(scale=scale)

            # Remove border
            fig_gca = figure.gca()
            fig_gca.set_frame_on(False)

            tax.boundary(linewidth=2.0)
            tax.heatmap(data, scale=scale, style="triangular", cmap="viridis_r")
            # tax.gridlines(color="blue", multiple=5)
            tax.set_title("{} - Mean of squared error sums - 30 pairs of lotteries - {} trials\n"
                          .format(self.monkey, self.n_trials), fontsize=13)

            font_size = 20
            offset = 0.15

            tax.bottom_axis_label(r"$r$", fontsize=font_size, offset=- offset / 4)
            tax.right_axis_label(r"$\tau$", fontsize=font_size, offset=offset)
            tax.left_axis_label(r"$\alpha$", fontsize=font_size, offset=offset)

            order = ["b", "r", "l"]  # Remain that order is bottom, right, left

            for i in range(3):
                ticks = ["%.2f" % i for i in
                         np.linspace(min(self.model_parameters[:, i]),
                                     max(self.model_parameters[:, i]),
                                     5)]

                offset = 0.028
                if i == 0:
                    offset /= 1.5
                tax.ticks(ticks=ticks, axis=order[i], linewidth=1, offset=offset)

            tax.clear_matplotlib_ticks()
            tax._redraw_labels()  # Bug in saving fig otherwise on Mac OSX

            plt.savefig(fig_name)
            plt.close()

    @staticmethod
    def plot(x, y, y_std, x_label, y_label, monkey, fig_name, x_lim=None, y_lim=None, parameter=None, n_trials=None):

        plt.plot(x, y, c='b', lw=2)
        plt.plot(x, y + y_std, c='b', lw=.5)
        plt.plot(x, y - y_std, c='b', lw=.5)
        plt.fill_between(x, y + y_std, y - y_std, color='b', alpha=.1)

        plt.xlabel("{}\n".format(x_label), fontsize=12)
        plt.ylabel("{}\n".format(y_label), fontsize=12)

        if x_lim:
            plt.xlim(x_lim)
        if y_lim:
            plt.ylim(y_lim)

        if parameter:
            plt.title("{} - {}".format(monkey, parameter))
        else:
            plt.title("{}".format(monkey))

        if n_trials:

            plt.text(x=min(x) + (max(x) - min(x)) * 0.5, y=0.4, s="Trials number: {}".format(n_trials))

        plt.xlim(min(x), max(x))

        plt.savefig(fig_name)

        plt.close()


class SimpleAnalysis(object):

    def __init__(self, monkey, figure_folder, exp_n_values, exp_k_values, lotteries):

        self.monkey = monkey
        self.exp_n_values = exp_n_values
        self.exp_k_values = exp_k_values
        self.lotteries = lotteries

        self.fig_folder = figure_folder

        self.X = []
        self.Y = []
        self.Y_std = []

        self.n_per_expected_value = {}
        self.k_per_expected_value = {}


    @staticmethod
    def expected_value(lottery):

        return lottery[0] * lottery[1]

    def _old_run(self):

        fig_name = "{}/{}_diff_expected_value.pdf".format(self.fig_folder, self.monkey)

        i = 0

        for l0, l1 in self.lotteries:

            diff_exp_value = self.expected_value(l0) - self.expected_value(l1)
            # print(diff_exp_value)
            if diff_exp_value not in self.X:
                self.X.append(diff_exp_value)

                self.n_per_expected_value[diff_exp_value] = 0
                self.k_per_expected_value[diff_exp_value] = 0

            self.n_per_expected_value[diff_exp_value] += self.exp_n_values[i]
            self.k_per_expected_value[diff_exp_value] += self.exp_k_values[i]

            i += 1

        for x in self.X:

            a = np.zeros(int(self.n_per_expected_value[x]))
            a[:int(self.k_per_expected_value[x])] = 1

            self.Y.append(np.mean(a))
            self.Y_std.append(np.std(a))

        Analysis.plot(x=self.X,
                      y=np.asarray(self.Y),
                      y_std=self.Y_std,
                      x_label="Difference in expected value between the riskiest option and the safest option",
                      y_label="Frequency of choosing riskiest option",
                      fig_name=fig_name,
                      monkey=self.monkey,
                      x_lim=[-1.25, 1.25],
                      y_lim=[-0.001, 1.001],
                      n_trials=np.sum(np.asarray([i for i in self.n_per_expected_value.values()], dtype=int)))

    @staticmethod
    def sigmoid(x, x0, k):
        y = 1 / (1 + np.exp(-k * (x - x0)))
        return y

    def run(self, force=False):

        fig_name = "{}/{}_diff_expected_value.pdf".format(self.fig_folder, self.monkey)

        if path.exists(fig_name) and not force:

            return

        n_trials = int(np.sum(self.exp_n_values))

        xdata = np.zeros(len(self.lotteries))
        ydata = np.zeros(len(self.lotteries))

        i = 0

        for l0, l1 in self.lotteries:

            diff_exp_value = self.expected_value(l0) - self.expected_value(l1)
            # print(diff_exp_value)

            xdata[i] = diff_exp_value
            ydata[i] = self.exp_k_values[i] / self.exp_n_values[i]

            i += 1

        # xdata = np.array([0.0, 1.0, 3.0, 4.3, 7.0, 8.0, 8.5, 10.0, 12.0])
        # ydata = np.array([0.01, 0.02, 0.04, 0.11, 0.43, 0.7, 0.89, 0.95, 0.99])

        popt, pcov = curve_fit(self.sigmoid, xdata, ydata)

        x = np.linspace(-1.25, 1.25, 50)
        y = self.sigmoid(x, *popt)

        plt.plot(xdata, ydata, 'o', color=(0., 0., 0.), label='data')
        plt.plot(x, y, color=(0., 0., 0.), label='fit')

        plt.xlim(-1.27, 1.27)
        plt.ylim(0, 1.)

        plt.title("{}\n".format(self.monkey))

        plt.xlabel("Difference in expected value between the riskiest option and the safest option")
        plt.ylabel("Frequency at which the riskiest option is chosen")

        plt.text(x=min(x) + (max(x) - min(x)) * 0.7, y=0.4, s="Trials number: {}".format(n_trials))

        # plt.legend(loc='best')
        plt.savefig(fig_name)
        plt.show()


def get_archetypes(database_name, database_folder, starting_point, incongruent_lotteries_couples_file, force=False):

    if path.exists(incongruent_lotteries_couples_file) and not force:

        incongruent_lotteries = np.load(incongruent_lotteries_couples_file)

    else:
        a = ArchetypeFinder(database_folder=database_folder, database_name=database_name, starting_point=starting_point)
        incongruent_lotteries = a.run()
        np.save(incongruent_lotteries_couples_file, incongruent_lotteries)

    return incongruent_lotteries


def get_model_parameters_and_p_values(model_parameters_file, model_p_values_file,
                                      lotteries, force=False):

    if path.exists(model_parameters_file) and path.exists(model_p_values_file) and not force:

        model_parameters = np.load(model_parameters_file)
        model_p_values = np.load(model_p_values_file)

    else:

        m = ModelRunner()
        model_parameters, model_p_values = m.run(lotteries)
        np.save(model_parameters_file, model_parameters)
        np.save(model_p_values_file, model_p_values)

    return model_parameters, model_p_values


def get_monkey_data(monkey, monkey_data_files, starting_point, database_folder, database_name, lotteries, force=False):

    if path.exists(monkey_data_files[monkey]["n"]) and path.exists(monkey_data_files[monkey]["k"]) and not force:

        n_per_lotteries = np.load(monkey_data_files[monkey]["n"])
        k_per_lotteries = np.load(monkey_data_files[monkey]["k"])

    else:

        d = DataGetter(database_folder=database_folder, database_name=database_name,
                       monkey=monkey, starting_point=starting_point)
        n_per_lotteries, k_per_lotteries = d.get_n_and_k_per_lotteries(lotteries)

        np.save(monkey_data_files[monkey]["n"], n_per_lotteries)
        np.save(monkey_data_files[monkey]["k"], k_per_lotteries)

    return n_per_lotteries, k_per_lotteries


def get_fit(model_parameters, model_p_values, exp_n_values, exp_k_values, monkey_data_files, monkey, force=False):

    if path.exists(monkey_data_files[monkey]["MLE"]) and path.exists(monkey_data_files[monkey]["LSE"]) and not force:

        lse_fit = np.load(monkey_data_files[monkey]["LSE"])
        mle_fit = np.load(monkey_data_files[monkey]["MLE"])

    else:

        fit = Fit(
            exp_k_values=exp_k_values, exp_n_values=exp_n_values,
            model_p_values=model_p_values, model_parameters=model_parameters)

        lse_fit = fit.run(method="LSE")
        np.save(monkey_data_files[monkey]["LSE"], lse_fit)

        mle_fit = fit.run(method="MLE")
        np.save(monkey_data_files[monkey]["MLE"], mle_fit)

    return lse_fit, mle_fit


def main():

    starting_point = "2016-08-11"
    database_folder = "../../results"
    figure_folder = "../../figures"
    database_name = "results_sequential"
    npy_files_folder = "../../analysis_sequential_npy_files"
    incongruent_lotteries_couples_file = "{}/{}.npy".format(npy_files_folder, "incongruent_lotteries_couples")
    model_p_values_file = "{}/{}.npy".format(npy_files_folder, "model_p_values")
    model_parameters_file = "{}/{}.npy".format(npy_files_folder, "model_parameters")

    monkey_data_files = {

        "Havane":
            {
                "n": "{}/{}.npy".format(npy_files_folder, "havane_data_n"),
                "k": "{}/{}.npy".format(npy_files_folder, "havane_data_k"),
                "LSE": "{}/{}.npy".format(npy_files_folder, "havane_fit_lse"),
                "MLE": "{}/{}.npy".format(npy_files_folder, "havane_fit_mle")
            },
        "Gladys":
            {
                "n": "{}/{}.npy".format(npy_files_folder, "gladys_data_n"),
                "k": "{}/{}.npy".format(npy_files_folder, "gladys_data_k"),
                "LSE": "{}/{}.npy".format(npy_files_folder, "gladys_fit_lse"),
                "MLE": "{}/{}.npy".format(npy_files_folder, "gladys_fit_mle")
            }
    }

    monkeys = ["Gladys"]

    incongruent_lotteries = \
        get_archetypes(database_folder=database_folder, database_name=database_name, starting_point=starting_point,
                       incongruent_lotteries_couples_file=incongruent_lotteries_couples_file)

    model_parameters, model_p_values = \
        get_model_parameters_and_p_values(model_parameters_file=model_parameters_file,
                                          model_p_values_file=model_p_values_file,
                                          lotteries=incongruent_lotteries)

    for monkey in monkeys:

        n_per_incongruent_lotteries, k_per_incongruent_lotteries = \
            get_monkey_data(monkey=monkey, monkey_data_files=monkey_data_files,
                            starting_point=starting_point,
                            database_folder=database_folder,
                            database_name=database_name,
                            lotteries=incongruent_lotteries)

        lse_fit, mle_fit = get_fit(
            model_parameters=model_parameters, model_p_values=model_p_values,
            exp_n_values=n_per_incongruent_lotteries,
            exp_k_values=k_per_incongruent_lotteries,
            monkey_data_files=monkey_data_files, monkey=monkey)

        a = Analysis(lse_fit=lse_fit, mle_fit=mle_fit, model_parameters=model_parameters, monkey=monkey,
                     figure_folder=figure_folder,
                     n_trials=int(np.sum(n_per_incongruent_lotteries)))

        a.lse_basic_analysis()
        a.lse_plot_error_according_to_parameter_values()
        a.lse_plot_phase_diagram()

        a.mle_plot_error_according_to_parameter_value()
        a.mle_plot_phase_diagram()
        a.mle_basic_analysis()

        b = SimpleAnalysis(monkey=monkey,
                           lotteries=incongruent_lotteries,
                           exp_n_values=n_per_incongruent_lotteries,
                           exp_k_values=k_per_incongruent_lotteries,
                           figure_folder=figure_folder)
        b.run()

if __name__ == "__main__":

    main()
