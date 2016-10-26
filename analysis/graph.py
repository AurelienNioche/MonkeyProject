from pylab import np, plt
from os import path, mkdir
from analysis import Analyst


def get_data(monkey, date):

    analyst = Analyst(database_name="../Results/results")
    results = analyst.analyse_single_session(monkey=monkey, date=date)
    return results


def represent_incongruent_trials(results, monkey, date, fig_name):

    x = np.array([-1.25, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1.25])
    y = np.zeros(len(x))
    y_std = np.zeros(len(x))

    n_trials = 0

    for i, diff in enumerate(x):
        # print(self.incongruent_trials_expect[i])
        # print(len(self.incongruent_trials_expect[i]))
        # print(np.mean(self.incongruent_trials_expect[i]))

        # diff: Incongruent difference expected value for 'risky' option.

        y[i] = np.mean(results[diff])
        y_std[i] = np.std(results[diff])

        n_trials += len(results[diff])

    plt.plot(x, y, c='b', lw=2)
    plt.plot(x, y + y_std, c='b', lw=.5)
    plt.plot(x, y - y_std, c='b', lw=.5)
    plt.fill_between(x, y + y_std, y - y_std, color='b', alpha=.1)

    plt.xlabel("Difference of expected value between the risky and safe options\n", fontsize=12)
    plt.ylabel("Frequency with which the risky option is chosen\n", fontsize=12)

    plt.title("{} - {}".format(monkey, date))

    mean_for_no_diff = np.mean(results[0])

    plt.hlines(mean_for_no_diff, min(x), 0, colors='k', linestyles='dotted')
    plt.vlines(0, min(y), mean_for_no_diff, colors='k', linestyles='dotted')

    plt.text(x=0.5, y=0.1, s="Trials number: {}".format(n_trials))

    plt.xlim(min(x), max(x))
    plt.ylim(0, 1.01)
    plt.savefig(fig_name)
    plt.show()

    plt.close()


def main():

    date = "2016/08/12"
    monkey = "Gladys"

    fig_folder = "../FigSingleSession"
    if not path.exists(fig_folder): mkdir(fig_folder)
    fig_name = "{}/{}_{}.pdf".format(fig_folder, monkey, date.replace("/", "-"))

    r = get_data(date=date, monkey=monkey)
    represent_incongruent_trials(r, monkey, date, fig_name)


if __name__ == "__main__":

    main()
